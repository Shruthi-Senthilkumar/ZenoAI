import pytest
from pydantic import ValidationError
from sqlmodel import Session

from backend.database import engine, ResumeBullet
from backend.logic.feedback import record_outcome_feedback
from backend.schemas.feedback import OutcomeFeedback
from backend.database import init_db


@pytest.fixture(autouse=True, scope="module")
def _ensure_db_initialized():
    init_db()


def _make_bullet(bullet_id: str):
    with Session(engine) as session:
        session.add(ResumeBullet(id=bullet_id, student_id="student-test", text="Test bullet."))
        session.commit()


@pytest.fixture(autouse=True)
def _cleanup_bullets():
    yield
    with Session(engine) as session:
        for row in session.query(ResumeBullet).filter(ResumeBullet.student_id == "student-test"):
            session.delete(row)
        session.commit()


@pytest.mark.parametrize("outcome", ["yes", "no", "somewhat"])
def test_record_outcome_feedback_accepts_all_three_literal_values(outcome):
    _make_bullet("bullet-1")
    result = record_outcome_feedback("bullet-1", outcome)
    assert isinstance(result, OutcomeFeedback)
    assert result.bullet_id == "bullet-1"
    assert result.outcome == outcome


def test_record_outcome_feedback_rejects_invalid_outcome():
    _make_bullet("bullet-1")
    with pytest.raises(ValidationError):
        record_outcome_feedback("bullet-1", "maybe")


def test_record_outcome_feedback_raises_for_missing_bullet():
    with pytest.raises(ValueError):
        record_outcome_feedback("does-not-exist", "yes")


def test_record_outcome_feedback_persists_to_real_db():
    _make_bullet("bullet-2")
    record_outcome_feedback("bullet-2", "yes")
    with Session(engine) as session:
        bullet = session.get(ResumeBullet, "bullet-2")
        assert bullet.outcome_feedback == "yes"


def test_multiple_feedback_events_persist_independently():
    _make_bullet("bullet-a")
    _make_bullet("bullet-b")
    _make_bullet("bullet-c")
    record_outcome_feedback("bullet-a", "yes")
    record_outcome_feedback("bullet-b", "no")
    record_outcome_feedback("bullet-c", "somewhat")
    with Session(engine) as session:
        outcomes = {
            b.id: b.outcome_feedback
            for b in session.query(ResumeBullet).filter(ResumeBullet.id.in_(["bullet-a", "bullet-b", "bullet-c"]))
        }
    assert outcomes == {"bullet-a": "yes", "bullet-b": "no", "bullet-c": "somewhat"}