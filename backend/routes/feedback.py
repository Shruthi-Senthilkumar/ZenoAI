"""POST /resume/bullets/{bullet_id}/feedback (PRD §4.19).

NOTE: this exact path is a documented extension, not something already
listed in the Frontend Spec §6 API Contract table (resume bullet
feedback isn't in it yet). Flagged for Thaariha to confirm/align on
the final path and payload shape — see the PR description.
"""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from backend.logic.feedback import record_outcome_feedback
from backend.schemas.feedback import OutcomeFeedback

router = APIRouter()


class OutcomeFeedbackRequest(BaseModel):
    outcome: Literal["yes", "no", "somewhat"]


@router.post("/resume/bullets/{bullet_id}/feedback", response_model=OutcomeFeedback)
def post_resume_bullet_feedback(bullet_id: str, payload: OutcomeFeedbackRequest) -> OutcomeFeedback:
    return record_outcome_feedback(bullet_id, payload.outcome)
