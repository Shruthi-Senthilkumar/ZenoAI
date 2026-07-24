import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.database import Student, engine, init_db
from backend.logic.intake import ExtractedProfile, IntakeState, extract_and_store_profile
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _ensure_db_initialized():
    init_db()


def test_profile_404s_for_student_who_never_did_intake():
    response = client.get("/intake/profile?student_id=never-did-intake")
    assert response.status_code == 404


def test_profile_404s_even_for_a_student_with_default_target_role(monkeypatch):
    """The real bug this test guards against: target_role/weekly_hours
    carry non-null defaults for every seeded student, so a null-check on
    those columns alone would incorrectly report a captured profile.
    Only intake_completed_at being set should flip this to 200."""
    from backend.database import create_or_update_student

    create_or_update_student(student_id="has-defaults-only", name="Defaults Only")
    response = client.get("/intake/profile?student_id=has-defaults-only")
    assert response.status_code == 404


def test_extraction_persists_camelcase_response_including_all_fields(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return ExtractedProfile(
            target_role="SDE",
            weekly_hours=8,
            timeline_months=6,
            education_level="Undergraduate",
            topic_levels={"arrays": "advanced", "recursion": "beginner"},
        )

    monkeypatch.setattr("backend.logic.intake.call_and_validate", fake_call_and_validate)

    extract_and_store_profile("extraction-test-student", IntakeState(answers=["SDE, 8 hours"]))

    response = client.get("/intake/profile?student_id=extraction-test-student")
    assert response.status_code == 200
    assert response.json() == {
        "targetRole": "SDE",
        "weeklyHours": 8,
        "timelineMonths": 6,
        "educationLevel": "Undergraduate",
        "topicLevels": {"arrays": "advanced", "recursion": "beginner"},
    }


def test_topic_levels_defaults_to_empty_object_when_none_evaluated(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return ExtractedProfile(target_role="Data", weekly_hours=5, timeline_months=3, education_level="Graduate")

    monkeypatch.setattr("backend.logic.intake.call_and_validate", fake_call_and_validate)

    extract_and_store_profile("no-topics-student", IntakeState(answers=["Data, 5 hours"]))

    response = client.get("/intake/profile?student_id=no-topics-student")
    assert response.json()["topicLevels"] == {}


def test_extraction_failure_does_not_mark_profile_complete(monkeypatch):
    from backend.llm.validation import LLMValidationFailed

    def raise_validation_failed(system_prompt, user_prompt, schema):
        raise LLMValidationFailed(schema.__name__)

    monkeypatch.setattr("backend.logic.intake.call_and_validate", raise_validation_failed)

    extract_and_store_profile("extraction-failure-student", IntakeState(answers=["something"]))

    response = client.get("/intake/profile?student_id=extraction-failure-student")
    assert response.status_code == 404


def test_intake_data_survives_a_later_github_connect(monkeypatch):
    """create_or_update_student is also called by the GitHub OAuth
    callback -- it must never silently clear or reset real intake data
    just because an unrelated field (github_username) is being updated
    at the same time.

    This specifically guards against a real bug found and fixed while
    adding timeline_months: target_role/weekly_hours used to be
    unconditionally overwritten with their default-arg values on every
    call to this helper, so connecting GitHub after intake (or simply
    a backend hot-reload re-running main.py's student-1 seed call)
    would silently reset a student's real captured role and weekly
    hours back to "Software Engineer" / 15.
    """
    from backend.database import create_or_update_student

    with Session(engine) as session:
        student = session.exec(select(Student).where(Student.id == "extraction-test-student")).first()
        assert student.intake_completed_at is not None
        assert student.education_level == "Undergraduate"
        assert student.target_role == "SDE"
        assert student.weekly_hours == 8
        assert student.timeline_months == 6
        original_timestamp = student.intake_completed_at

    create_or_update_student(
        student_id="extraction-test-student", name="Test", github_username="some-github-user"
    )

    with Session(engine) as session:
        student = session.exec(select(Student).where(Student.id == "extraction-test-student")).first()
        assert student.intake_completed_at == original_timestamp
        assert student.education_level == "Undergraduate"
        assert student.target_role == "SDE"
        assert student.weekly_hours == 8
        assert student.timeline_months == 6
        assert student.github_username == "some-github-user"