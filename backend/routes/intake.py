"""POST /intake/turn (Backend Spec §7)."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.logic.intake import next_intake_turn
from backend.schemas.intake import IntakeTurnResponse

router = APIRouter()


class IntakeTurnRequest(BaseModel):
    student_id: str
    last_answer: str = ""


@router.post("/intake/turn", response_model=IntakeTurnResponse)
def post_intake_turn(payload: IntakeTurnRequest) -> IntakeTurnResponse:
    return next_intake_turn(payload.student_id, payload.last_answer)
