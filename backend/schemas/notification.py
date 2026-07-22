"""In-App Notification Banner schema (PRD §4.17)."""

from typing import Literal

from pydantic import BaseModel


class NotificationBanner(BaseModel):
    type: Literal["streak-at-risk", "resume-bullet-ready", "reminder", "offline"]
    message: str
    priority: int
