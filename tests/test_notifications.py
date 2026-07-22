import pytest

from backend.logic.notifications import db as notif_db
from backend.logic.notifications import get_active_notification
from backend.logic.streak import db as streak_db
from backend.logic.struggle_detector import db as struggle_db


@pytest.fixture(autouse=True)
def _reset_stub_dbs():
    streak_db._STREAK_COUNT.clear()
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY.clear()
    struggle_db._QUIZ_SCORES.clear()
    struggle_db._DAYS_SINCE_LAST_COMMIT.clear()
    notif_db._RESUME_BULLET_READY.clear()
    notif_db._ASSIGNMENT_DUE_TOMORROW.clear()
    yield
    streak_db._STREAK_COUNT.clear()
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY.clear()
    struggle_db._QUIZ_SCORES.clear()
    struggle_db._DAYS_SINCE_LAST_COMMIT.clear()
    notif_db._RESUME_BULLET_READY.clear()
    notif_db._ASSIGNMENT_DUE_TOMORROW.clear()


def test_streak_at_risk_wins_over_everything_when_all_active():
    streak_db._STREAK_COUNT["s1"] = 5
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY["s1"] = 25.0
    notif_db._RESUME_BULLET_READY["s1"] = True
    notif_db._ASSIGNMENT_DUE_TOMORROW["s1"] = True

    banner = get_active_notification("s1")

    assert banner is not None
    assert banner.type == "streak-at-risk"
    assert banner.priority == 1


def test_resume_bullet_ready_wins_over_reminder_when_streak_not_at_risk():
    streak_db._STREAK_COUNT["s2"] = 0  # no streak -> not at risk regardless of hours
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY["s2"] = 25.0
    notif_db._RESUME_BULLET_READY["s2"] = True
    notif_db._ASSIGNMENT_DUE_TOMORROW["s2"] = True

    banner = get_active_notification("s2")

    assert banner is not None
    assert banner.type == "resume-bullet-ready"
    assert banner.priority == 2


def test_reminder_fires_when_only_reminder_signal_active():
    streak_db._STREAK_COUNT["s3"] = 0
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY["s3"] = 0.0
    notif_db._RESUME_BULLET_READY["s3"] = False
    notif_db._ASSIGNMENT_DUE_TOMORROW["s3"] = True

    banner = get_active_notification("s3")

    assert banner is not None
    assert banner.type == "reminder"
    assert banner.priority == 3
    assert banner.message == "Assignment due tomorrow"


def test_reminder_reuses_struggle_detector_career_signal_without_duplicating_logic():
    streak_db._STREAK_COUNT["s4"] = 0
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY["s4"] = 0.0
    notif_db._RESUME_BULLET_READY["s4"] = False
    notif_db._ASSIGNMENT_DUE_TOMORROW["s4"] = False
    struggle_db._QUIZ_SCORES["s4"] = []
    struggle_db._DAYS_SINCE_LAST_COMMIT["s4"] = 3  # > 2, struggle-detector's own threshold

    banner = get_active_notification("s4")

    assert banner is not None
    assert banner.type == "reminder"
    assert "3 days" in banner.message  # same reason text struggle-detector generates, reflecting the real gap


def test_streak_at_risk_does_not_fire_when_streak_is_zero():
    streak_db._STREAK_COUNT["s5"] = 0
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY["s5"] = 30.0

    banner = get_active_notification("s5")

    assert banner is None or banner.type != "streak-at-risk"


def test_streak_at_risk_does_not_fire_within_grace_window():
    streak_db._STREAK_COUNT["s6"] = 3
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY["s6"] = 5.0  # well under 20h

    banner = get_active_notification("s6")

    assert banner is None or banner.type != "streak-at-risk"


def test_none_returned_when_no_signals_active():
    streak_db._STREAK_COUNT["s7"] = 0
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY["s7"] = 0.0
    notif_db._RESUME_BULLET_READY["s7"] = False
    notif_db._ASSIGNMENT_DUE_TOMORROW["s7"] = False
    struggle_db._QUIZ_SCORES["s7"] = []
    struggle_db._DAYS_SINCE_LAST_COMMIT["s7"] = 0

    banner = get_active_notification("s7")

    assert banner is None


def test_max_one_banner_route_shape():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from backend.routes.notifications import router

    streak_db._STREAK_COUNT["s8"] = 2
    streak_db._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY["s8"] = 21.0

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    body = client.get("/notifications", params={"student_id": "s8"}).json()

    assert set(body.keys()) == {"banner"}
    assert isinstance(body["banner"], dict)  # exactly one banner object, never a list


def test_route_returns_null_banner_when_nothing_active():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from backend.routes.notifications import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    body = client.get("/notifications", params={"student_id": "no-signals-student"}).json()

    assert body == {"banner": None}
