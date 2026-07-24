import json

import pytest

from backend.database import create_or_update_student, init_db
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _ensure_db_initialized():
    init_db()


def test_falls_back_to_mock_when_adzuna_keys_not_configured(monkeypatch):
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)

    response = client.get("/jobs?student_id=jobs-fallback-student")
    assert response.status_code == 200
    listings = response.json()
    assert len(listings) > 0
    assert any(job["source"] in ("Adzuna", "JSearch") for job in listings)


def test_skill_match_reflects_real_evaluated_intake_data_not_hardcoded(monkeypatch):
    """The real bug this guards against: student_skills used to be a
    hardcoded list identical for every student regardless of who asked.
    A student with zero evaluated topics should get 0% match against
    any listing that requires skills; a student with a matching
    evaluated topic should score higher on the same listing.

    Forces the mock-fallback path explicitly (unsets Adzuna keys) so
    this test is deterministic regardless of whether the machine
    running it has real Adzuna credentials configured or not.
    """
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)

    create_or_update_student(student_id="jobs-no-skills-student", name="No Skills")
    create_or_update_student(
        student_id="jobs-has-skills-student",
        name="Has Skills",
        topic_levels_json=json.dumps({"python-basics": "advanced"}),
    )

    no_skills_response = client.get("/jobs?student_id=jobs-no-skills-student").json()
    has_skills_response = client.get("/jobs?student_id=jobs-has-skills-student").json()

    python_job_no_skills = next((j for j in no_skills_response if "Python" in str(j)), None)
    python_job_has_skills = next(
        (j for j in has_skills_response if j["title"] == "Backend Developer Intern"), None
    )

    assert python_job_no_skills is not None
    assert python_job_has_skills is not None
    assert python_job_has_skills["match_pct"] > python_job_no_skills["match_pct"]


def test_live_adzuna_call_used_when_configured_and_healthy(monkeypatch):
    monkeypatch.setenv("ADZUNA_APP_ID", "fake_id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "fake_key")

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "results": [
                    {
                        "id": "adz-live-1",
                        "title": "Live SDE Intern",
                        "company": {"display_name": "LiveCo"},
                        "description": "Python and SQL required.",
                    }
                ]
            }

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url, params=None, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("backend.routes.jobs.httpx.Client", lambda timeout=8.0: FakeClient())

    response = client.get("/jobs?student_id=jobs-live-test-student")
    listings = response.json()
    assert any(j["source"] == "Adzuna" and j["title"] == "Live SDE Intern" for j in listings)


def test_falls_back_to_mock_when_live_adzuna_call_fails(monkeypatch):
    monkeypatch.setenv("ADZUNA_APP_ID", "fake_id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "fake_key")

    class FailingClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url, params=None, **kwargs):
            raise ConnectionError("simulated network failure")

    monkeypatch.setattr("backend.routes.jobs.httpx.Client", lambda timeout=8.0: FailingClient())

    response = client.get("/jobs?student_id=jobs-failure-test-student")
    assert response.status_code == 200
    listings = response.json()
    assert len(listings) > 0  # never blank, falls back to mock