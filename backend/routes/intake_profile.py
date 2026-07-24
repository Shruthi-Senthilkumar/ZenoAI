"""GET /intake/profile — reads the structured profile back off the real
Student row that extract_and_store_profile() (backend/logic/intake.py)
writes to once intake completes.

Response is camelCase, matching the existing precedent set by
backend/logic/tasks.py's TaskItem/StreakState/ReadinessState models.

404s until intake_completed_at is actually set — target_role/
weekly_hours themselves are never null (they carry defaults for every
seeded student), so checking those directly would incorrectly report
a captured profile for a student who never did intake.

topicLevels is the evaluated (not self-reported) per-topic skill
assessment from the diagnostic questions — stored as a JSON string on
Student.topic_levels_json, parsed back into a real object here.
"""
import json

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.database import Student, engine

router = APIRouter()


class IntakeProfileResponse(BaseModel):
    target_role: str = Field(serialization_alias="targetRole")
    weekly_hours: int = Field(serialization_alias="weeklyHours")
    timeline_months: int = Field(serialization_alias="timelineMonths")
    education_level: str = Field(serialization_alias="educationLevel")
    topic_levels: dict[str, str] = Field(default_factory=dict, serialization_alias="topicLevels")

    class Config:
        populate_by_name = True


@router.get("/intake/profile", response_model=IntakeProfileResponse, response_model_by_alias=True)
def get_intake_profile(student_id: str = Query(...)) -> IntakeProfileResponse:
    with Session(engine) as session:
        student = session.exec(select(Student).where(Student.id == student_id)).first()
        if student is None or not student.intake_completed_at:
            raise HTTPException(404, "No completed intake profile found for this student")
        try:
            topic_levels = json.loads(student.topic_levels_json) if student.topic_levels_json else {}
        except json.JSONDecodeError:
            topic_levels = {}
        return IntakeProfileResponse(
            target_role=student.target_role,
            weekly_hours=student.weekly_hours,
            timeline_months=student.timeline_months or 3,
            education_level=student.education_level or "Undergraduate",
            topic_levels=topic_levels,
        )