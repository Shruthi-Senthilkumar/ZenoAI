import pytest
from fastapi.testclient import TestClient

from backend.database import init_db
from backend.schemas.resume import ResumeBulletResponse
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _ensure_db_initialized():
    init_db()


def test_empty_list_for_student_with_no_bullets_yet():
    response = client.get("/resume/bullets?student_id=no-bullets-yet-student")
    assert response.status_code == 200
    assert response.json() == []


def test_generated_bullet_appears_in_the_list(monkeypatch):
    import backend.logic.resume as resume_mod

    monkeypatch.setattr(
        "backend.logic.resume.call_and_validate",
        lambda *a, **k: ResumeBulletResponse(
            text="Built and shipped a feature.", evidence_link="https://github.com/student/repo"
        ),
    )

    resume_mod.generate_resume_bullet("route-test-student", "oop", "https://github.com/student/repo")

    response = client.get("/resume/bullets?student_id=route-test-student")
    assert response.status_code == 200
    bullets = response.json()
    assert len(bullets) == 1
    assert bullets[0]["text"] == "Built and shipped a feature."
    assert bullets[0]["evidence_link"] == "https://github.com/student/repo"
    assert "id" in bullets[0]


def test_deferred_failure_never_creates_a_bullet_row(monkeypatch):
    import backend.logic.resume as resume_mod
    from backend.llm.validation import LLMValidationFailed

    def raise_validation_failed(*a, **k):
        raise LLMValidationFailed("ResumeBulletResponse")

    monkeypatch.setattr("backend.logic.resume.call_and_validate", raise_validation_failed)

    result = resume_mod.generate_resume_bullet("deferred-test-student", "oop", "https://github.com/student/repo")
    assert result is None

    response = client.get("/resume/bullets?student_id=deferred-test-student")
    assert response.json() == []


def test_bullets_are_scoped_to_the_requesting_student(monkeypatch):
    import backend.logic.resume as resume_mod

    monkeypatch.setattr(
        "backend.logic.resume.call_and_validate",
        lambda *a, **k: ResumeBulletResponse(text="Student one's bullet.", evidence_link="https://x/1"),
    )
    resume_mod.generate_resume_bullet("scoped-student-one", "oop", "https://x/1")

    response = client.get("/resume/bullets?student_id=scoped-student-two")
    assert response.json() == []