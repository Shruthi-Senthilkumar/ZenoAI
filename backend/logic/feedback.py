"""Outcome Feedback Loop stub (PRD §4.19).

Lightweight check-in after a resume bullet is generated: "Did this help
in an interview?" Resume bullet generation and storage themselves are
Subhiksha's scope (Integration Spec §4/§9) — this is only the feedback
capture stub, recording the check-in response against a bullet_id.
"""

from pydantic import BaseModel

from backend.schemas.feedback import OutcomeFeedback


class OutcomeFeedbackEvent(BaseModel):
    bullet_id: str
    outcome: str


class _StubDB:
    """In-memory fixture stand-in for Subhiksha's DB layer (outcome_feedback_events table)."""

    def __init__(self) -> None:
        self._EVENTS: list[OutcomeFeedbackEvent] = []

    def insert(self, event: OutcomeFeedbackEvent) -> None:
        self._EVENTS.append(event)

    def get_events(self, bullet_id: str | None = None) -> list[OutcomeFeedbackEvent]:
        if bullet_id is None:
            return list(self._EVENTS)
        return [e for e in self._EVENTS if e.bullet_id == bullet_id]


db = _StubDB()


def record_outcome_feedback(bullet_id: str, outcome: str) -> OutcomeFeedback:
    feedback = OutcomeFeedback(bullet_id=bullet_id, outcome=outcome)
    db.insert(OutcomeFeedbackEvent(bullet_id=bullet_id, outcome=outcome))
    return feedback
