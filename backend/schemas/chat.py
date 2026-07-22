"""Mentor AI Chat schema (Backend Spec §12)."""

from pydantic import BaseModel


class ChatReplyResponse(BaseModel):
    reply: str
