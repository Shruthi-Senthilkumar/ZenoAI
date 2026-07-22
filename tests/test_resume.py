import pytest

from backend.llm.validation import LLMValidationFailed
from backend.logic.notifications import db as notif_db
from backend.logic.resume import generate_resume_bullet
from backend.schemas.resume import ResumeBulletResponse


@pytest.fixture(autouse=True)
def _reset_notification_stub():
    notif_db._RESUME_BULLET_READY.clear()
    yield
    notif_db._RESUME_BULLET_READY.clear()


def test_generate_resume_bullet_returns_validated_response_from_mocked_groq(monkeypatch):
    fake_response = ResumeBulletResponse(
        text="Implemented a graph-traversal pathfinder achieving O(V+E) complexity.",
        evidence_link="https://github.com/student/leetcode-practice/commit/abc123",
    )

    def fake_call_and_validate(system_prompt, user_prompt, schema):
        assert schema is ResumeBulletResponse
        assert "dsa-graphs" in user_prompt
        assert "https://github.com/student/leetcode-practice/commit/abc123" in user_prompt
        return fake_response

    monkeypatch.setattr("backend.logic.resume.call_and_validate", fake_call_and_validate)

    result = generate_resume_bullet(
        "student-1", "dsa-graphs", "https://github.com/student/leetcode-practice/commit/abc123"
    )

    assert result == fake_response


def test_generate_resume_bullet_preserves_the_given_evidence_link(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return ResumeBulletResponse(text="Built a REST API.", evidence_link="https://github.com/student/repo")

    monkeypatch.setattr("backend.logic.resume.call_and_validate", fake_call_and_validate)

    result = generate_resume_bullet("student-1", "oop", "https://github.com/student/repo")

    assert result.evidence_link == "https://github.com/student/repo"


def test_generate_resume_bullet_fallback_defers_rather_than_showing_partial_bullet(monkeypatch):
    def raise_validation_failed(system_prompt, user_prompt, schema):
        raise LLMValidationFailed(schema.__name__)

    monkeypatch.setattr("backend.logic.resume.call_and_validate", raise_validation_failed)

    result = generate_resume_bullet("student-1", "dsa-graphs", "https://github.com/student/repo")

    assert result is None  # deferred to next completed-module trigger, no partial bullet shown


def test_successful_generation_marks_resume_bullet_ready(monkeypatch):
    """Item 2 (master prompt): the resume-bullet-ready notification flag
    was previously a dead stub, never set by anything. A genuine success
    must flip it."""

    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return ResumeBulletResponse(text="Built a REST API.", evidence_link="https://github.com/student/repo")

    monkeypatch.setattr("backend.logic.resume.call_and_validate", fake_call_and_validate)

    assert notif_db.has_unseen_resume_bullet("student-notif") is False

    generate_resume_bullet("student-notif", "oop", "https://github.com/student/repo")

    assert notif_db.has_unseen_resume_bullet("student-notif") is True


def test_deferred_failure_does_not_mark_resume_bullet_ready(monkeypatch):
    """The flag must only flip on genuine success, never on a deferred
    LLMValidationFailed — a partial/failed attempt is not a real bullet."""

    def raise_validation_failed(system_prompt, user_prompt, schema):
        raise LLMValidationFailed(schema.__name__)

    monkeypatch.setattr("backend.logic.resume.call_and_validate", raise_validation_failed)

    generate_resume_bullet("student-notif-2", "dsa-graphs", "https://github.com/student/repo")

    assert notif_db.has_unseen_resume_bullet("student-notif-2") is False


def test_resume_bullet_ready_flows_end_to_end_into_get_active_notification(monkeypatch):
    """Full loop: generate a bullet -> flag flips -> notification check
    surfaces it at priority 2 -> flag clears once surfaced."""
    from backend.logic.notifications import get_active_notification
    from backend.logic.streak import db as streak_db

    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return ResumeBulletResponse(text="Shipped a feature.", evidence_link="https://github.com/student/repo")

    monkeypatch.setattr("backend.logic.resume.call_and_validate", fake_call_and_validate)

    streak_db._STREAK_COUNT["student-e2e"] = 0  # keep streak-at-risk from outranking it
    notif_db._ASSIGNMENT_DUE_TOMORROW["student-e2e"] = False

    generate_resume_bullet("student-e2e", "oop", "https://github.com/student/repo")

    banner = get_active_notification("student-e2e")
    assert banner is not None
    assert banner.type == "resume-bullet-ready"
    assert banner.priority == 2

    # Second read: already surfaced once, should not repeat.
    banner_again = get_active_notification("student-e2e")
    assert banner_again is None or banner_again.type != "resume-bullet-ready"
