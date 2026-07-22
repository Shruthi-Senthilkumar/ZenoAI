"""Outcome Feedback Loop schema (PRD §4.19)."""

from typing import Literal

from pydantic import BaseModel


class OutcomeFeedback(BaseModel):
    bullet_id: str
    outcome: Literal["yes", "no", "somewhat"]
