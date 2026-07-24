"""GET /resume/bullets — lists all resume bullets generated so far for a
student, from the real ResumeBullet table that generate_resume_bullet()
(backend/logic/resume.py) now actually writes to.

Response fields deliberately kept snake_case (id, text, evidence_link)
to match lib/types.ts's ResumeBullet interface exactly — that type
was already written to mirror this table's real columns, unlike
JobListing's camelCase guess against a route that didn't exist yet
when it was written. No aliasing needed here.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.database import ResumeBullet, engine

router = APIRouter()


class ResumeBulletItem(BaseModel):
    id: str
    text: str
    evidence_link: str


@router.get("/resume/bullets", response_model=list[ResumeBulletItem])
def get_resume_bullets(student_id: str = Query(...)) -> list[ResumeBulletItem]:
    with Session(engine) as session:
        rows = session.exec(
            select(ResumeBullet)
            .where(ResumeBullet.student_id == student_id)
            .order_by(ResumeBullet.created_at.desc())
        ).all()
        return [ResumeBulletItem(id=r.id, text=r.text, evidence_link=r.evidence_link) for r in rows]