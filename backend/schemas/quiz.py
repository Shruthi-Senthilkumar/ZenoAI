"""Daily Micro-Test Generator schema (Backend Spec §8, PRD §4.9)."""

from pydantic import BaseModel


class MicroTestQuestion(BaseModel):
    q: str
    options: list[str]
    answer: str


class MicroTestResponse(BaseModel):
    topic: str
    questions: list[MicroTestQuestion]
