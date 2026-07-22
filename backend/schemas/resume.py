"""Resume Bullet schema (Backend Spec §3)."""

from pydantic import BaseModel


class ResumeBulletResponse(BaseModel):
    text: str
    evidence_link: str
