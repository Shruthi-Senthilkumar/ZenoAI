"""GET /roadmap (Backend Spec §6)."""

from fastapi import APIRouter

from backend.logic.roadmap import generate_roadmap

router = APIRouter()


@router.get("/roadmap")
def get_roadmap(student_id: str) -> dict:
    days = generate_roadmap(student_id)
    return {"days": [d.model_dump() for d in days]}
