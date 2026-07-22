import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.logic.readiness import ReadinessResult
from backend.logic.streak import db as streak_db
from backend.routes.dashboard import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_streak_db():
    streak_db._STREAK_COUNT.clear()
    yield
    streak_db._STREAK_COUNT.clear()


def test_dashboard_returns_both_readiness_scores_never_blended(monkeypatch):
    calls = []

    def fake_compute_readiness(student_id, goal_type):
        calls.append(goal_type)
        if goal_type == "academic":
            return ReadinessResult(score=0.71, confidence="medium")
        return ReadinessResult(score=0.54, confidence="medium")

    monkeypatch.setattr("backend.routes.dashboard.compute_readiness", fake_compute_readiness)

    response = client.get("/dashboard/student-1")

    assert response.status_code == 200
    body = response.json()
    assert body["academic"]["readiness"] == 0.71
    assert body["career"]["readiness"] == 0.54
    # each goal type computed via its own call — never averaged/blended into one number
    assert calls == ["academic", "career"]
    assert body["academic"]["readiness"] != body["career"]["readiness"]


def test_dashboard_response_matches_api_contract_shape(monkeypatch):
    def fake_compute_readiness(student_id, goal_type):
        return ReadinessResult(score=0.6, confidence="medium")

    monkeypatch.setattr("backend.routes.dashboard.compute_readiness", fake_compute_readiness)

    body = client.get("/dashboard/student-1").json()

    assert set(body.keys()) == {"academic", "career"}
    assert set(body["academic"].keys()) == {"readiness", "confidence", "subjects"}
    assert set(body["career"].keys()) == {"readiness", "confidence", "activity_trend", "streak"}


def test_dashboard_low_confidence_empty_state_never_hides_behind_bare_zero():
    # unknown student -> Phase 1's stub has no evidence -> score 0, confidence "low"
    body = client.get("/dashboard/no-such-student").json()

    assert body["academic"]["readiness"] == 0
    assert body["academic"]["confidence"] == "low"
    assert body["career"]["readiness"] == 0
    assert body["career"]["confidence"] == "low"
    # the confidence signal is always present alongside the score, however thin the evidence
    assert "confidence" in body["academic"] and "confidence" in body["career"]


def test_dashboard_includes_current_streak_count_in_career_panel():
    streak_db._STREAK_COUNT["student-1"] = 7

    body = client.get("/dashboard/student-1").json()

    assert body["career"]["streak"] == 7


def test_dashboard_unknown_student_streak_defaults_to_zero():
    body = client.get("/dashboard/never-seen-student").json()

    assert body["career"]["streak"] == 0
