"""Outcome Feedback Loop (PRD §4.19; docs/BACKEND_SPEC_ADDENDUM.md §14).

Assigned to Shruthi in the PRD's own Phase 4 table (§5) but never given a
numbered section in the Backend Spec doc — see the addendum for the
write-up this module was missing.

Lightweight check-in after a resume bullet is generated: "Did this help
in an interview?" Resume bullet generation and storage themselves are
Subhiksha's scope (Integration Spec §4/§9) — this is only the feedback
capture logic, recording the check-in response against a bullet_id in
the real resume_bullets table.
"""
from sqlmodel import Session, select

from backend.database import engine, ResumeBullet
from backend.schemas.feedback import OutcomeFeedback


def record_outcome_feedback(bullet_id: str, outcome: str) -> OutcomeFeedback:
    with Session(engine) as session:
        bullet = session.exec(select(ResumeBullet).where(ResumeBullet.id == bullet_id)).first()
        if bullet is None:
            raise ValueError(f"No resume bullet with id {bullet_id}")
        bullet.outcome_feedback = outcome
        session.add(bullet)
        session.commit()
    return OutcomeFeedback(bullet_id=bullet_id, outcome=outcome)