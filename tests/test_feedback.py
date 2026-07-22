import pytest
from pydantic import ValidationError

from backend.logic.feedback import db, record_outcome_feedback
from backend.schemas.feedback import OutcomeFeedback


@pytest.fixture(autouse=True)
def _reset_stub_db():
    db._EVENTS.clear()
    yield
    db._EVENTS.clear()


@pytest.mark.parametrize("outcome", ["yes", "no", "somewhat"])
def test_record_outcome_feedback_accepts_all_three_literal_values(outcome):
    result = record_outcome_feedback("bullet-1", outcome)

    assert isinstance(result, OutcomeFeedback)
    assert result.bullet_id == "bullet-1"
    assert result.outcome == outcome


def test_record_outcome_feedback_rejects_invalid_outcome():
    with pytest.raises(ValidationError):
        record_outcome_feedback("bullet-1", "maybe")


def test_record_outcome_feedback_persists_to_stub_db():
    record_outcome_feedback("bullet-2", "yes")

    events = db.get_events("bullet-2")
    assert len(events) == 1
    assert events[0].bullet_id == "bullet-2"
    assert events[0].outcome == "yes"


def test_multiple_feedback_events_persist_independently():
    record_outcome_feedback("bullet-a", "yes")
    record_outcome_feedback("bullet-b", "no")
    record_outcome_feedback("bullet-c", "somewhat")

    all_events = db.get_events()
    outcomes_by_bullet = {e.bullet_id: e.outcome for e in all_events}
    assert outcomes_by_bullet == {"bullet-a": "yes", "bullet-b": "no", "bullet-c": "somewhat"}
