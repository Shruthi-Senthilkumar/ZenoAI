import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.logic.tasks import (
    MAX_TASKS_PER_DAY,
    complete_task,
    db,
    get_today_response,
    get_today_tasks,
    stable_task_id,
)
from backend.logic.streak import db as streak_db
from backend.routes.tasks import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_stub_dbs():
    db._TASK_STATUS.clear()
    db._TASK_META.clear()
    streak_db._STREAK_COUNT.clear()
    streak_db._ACADEMIC_DONE_TODAY.clear()
    streak_db._CAREER_ACTIVE_TODAY.clear()
    streak_db._LAST_INCREMENTED_DATE.clear()
    yield
    db._TASK_STATUS.clear()
    db._TASK_META.clear()
    streak_db._STREAK_COUNT.clear()
    streak_db._ACADEMIC_DONE_TODAY.clear()
    streak_db._CAREER_ACTIVE_TODAY.clear()
    streak_db._LAST_INCREMENTED_DATE.clear()


def test_get_today_tasks_never_exceeds_the_cap():
    tasks = get_today_tasks("student-1")
    assert 1 <= len(tasks) <= MAX_TASKS_PER_DAY


def test_task_ids_are_stable_across_repeated_calls():
    first = get_today_tasks("student-1")
    second = get_today_tasks("student-1")
    assert [t.id for t in first] == [t.id for t in second]


def test_task_item_uses_camel_case_wire_fields():
    tasks = get_today_tasks("student-1")
    body = tasks[0].model_dump()
    assert set(body.keys()) == {"id", "goalType", "title", "reason", "status"}


def test_today_response_shape_matches_contract():
    response = get_today_response("student-1")
    body = response.model_dump()
    assert set(body.keys()) == {"tasks", "streak", "readiness"}
    assert set(body["streak"].keys()) == {"count", "academicDone", "careerActive"}
    assert set(body["readiness"].keys()) == {"academic", "career", "confidence"}


def test_readiness_scores_stay_separate_never_blended():
    response = get_today_response("student-1")
    assert response.readiness.academic != response.readiness.career


def test_complete_task_marks_status_done_on_next_fetch():
    tasks = get_today_tasks("student-1")
    task_id = tasks[0].id

    complete_task("student-1", task_id)

    refreshed = get_today_tasks("student-1")
    matched = next(t for t in refreshed if t.id == task_id)
    assert matched.status == "done"


def test_complete_task_triggers_dual_gate_streak_check():
    streak_db._ACADEMIC_DONE_TODAY["s-dual"] = False
    streak_db._CAREER_ACTIVE_TODAY["s-dual"] = True  # career already logged today
    streak_db._STREAK_COUNT["s-dual"] = 2

    tasks = get_today_tasks("s-dual")
    academic_task = next(t for t in tasks if t.goalType == "academic")

    complete_task("s-dual", academic_task.id)

    assert streak_db.get_streak_count("s-dual") == 3  # dual gate now satisfied -> incremented


def test_complete_task_does_not_increment_streak_without_career_activity():
    streak_db._ACADEMIC_DONE_TODAY["s-solo"] = False
    streak_db._CAREER_ACTIVE_TODAY["s-solo"] = False
    streak_db._STREAK_COUNT["s-solo"] = 2

    tasks = get_today_tasks("s-solo")
    academic_task = next(t for t in tasks if t.goalType == "academic")

    complete_task("s-solo", academic_task.id)

    assert streak_db.get_streak_count("s-solo") == 2  # career gate still unmet


def test_complete_task_on_unknown_task_id_does_not_crash():
    complete_task("student-1", "never-seen-task-id")  # must not raise
    assert db.get_task_status("never-seen-task-id") == "done"


def test_stable_task_id_is_deterministic_and_scoped_per_student():
    id_a = stable_task_id("student-1", "2026-07-22", "academic", "limits")
    id_b = stable_task_id("student-1", "2026-07-22", "academic", "limits")
    id_c = stable_task_id("student-2", "2026-07-22", "academic", "limits")
    assert id_a == id_b
    assert id_a != id_c


def test_route_get_tasks_today_matches_contract_shape():
    body = client.get("/tasks/today", params={"student_id": "student-1"}).json()
    assert set(body.keys()) == {"tasks", "streak", "readiness"}
    assert len(body["tasks"]) <= MAX_TASKS_PER_DAY


def test_route_post_complete_returns_ok_status():
    tasks = client.get("/tasks/today", params={"student_id": "student-1"}).json()["tasks"]
    task_id = tasks[0]["id"]

    response = client.post(f"/tasks/{task_id}/complete", json={"student_id": "student-1"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
