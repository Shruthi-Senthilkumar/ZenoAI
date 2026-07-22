"""POST /quiz/generate (Backend Spec §8)."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from backend.logic.quiz_gen import generate_quiz
from backend.schemas.quiz import MicroTestResponse

router = APIRouter()


class QuizGenerateRequest(BaseModel):
    topic: str
    goal_type: Literal["academic", "career"]


@router.post("/quiz/generate", response_model=MicroTestResponse)
def post_quiz_generate(payload: QuizGenerateRequest) -> MicroTestResponse:
    return generate_quiz(payload.topic, payload.goal_type)
