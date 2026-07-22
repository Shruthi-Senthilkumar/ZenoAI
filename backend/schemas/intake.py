"""Adaptive Diagnostic Intake schema (Backend Spec §7, PRD §4.3)."""

from pydantic import BaseModel


class IntakeTurnResponse(BaseModel):
    next_question: str | None  # null when intake is complete
    quick_replies: list[str] = []
    done: bool
