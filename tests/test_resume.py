from backend.llm.validation import LLMValidationFailed
from backend.logic.resume import generate_resume_bullet
from backend.schemas.resume import ResumeBulletResponse


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
