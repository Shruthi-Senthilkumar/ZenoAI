"""Today's Task Tracker (item 6) — the core loop's backend.

Materializes the front of a student's roadmap into addressable
TaskItem records with a stable ID and a completion status, backing
GET /tasks/today and POST /tasks/{id}/complete. Reuses Phase 1-4's
roadmap, readiness, and streak logic rather than re-deriving any of
it — this module only adds task identity and completion tracking on
top.

"Today" is the front MAX_TASKS_PER_DAY items of generate_roadmap()'s
chronologically-sorted output, not a strict filter on items literally
dated today: the roadmap can have slack days (§6, item 2b) where
nothing lands exactly on today's date, and Today is meant to always
show the student something actionable — "never a menu screen" — so
pinning the queue's front matches that better than risking an empty
screen. Each track schedules at most 1 item/day, so this is almost
always exactly what's dated today in practice.

TaskItem/StreakState/ReadinessState field names are camelCase
(goalType, academicDone, careerActive) to match the Frontend Spec §6
wire contract exactly, rather than Python-idiomatic snake_case with a
serialization alias — one less thing to forget when a route or test
serializes this model.

Subhiksha's DB isn't live yet, so per-task completion state and task
metadata are stubbed with an in-memory _StubDB — swap-in-ready for a
real DB later, same pattern as prior phases.
"""

import hashlib
from typing import Literal

from pydantic import BaseModel

from backend.logic.readiness import compute_readiness
from backend.logic.roadmap import RoadmapDay, generate_roadmap
from backend.logic.streak import check_streak_increment
from backend.logic.streak import db as streak_db

MAX_TASKS_PER_DAY = 3

TaskStatus = Literal["default", "in_progress", "done", "overdue"]

_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


class TaskItem(BaseModel):
    id: str
    goalType: Literal["academic", "career"]
    title: str
    reason: str
    status: TaskStatus = "default"


class StreakState(BaseModel):
    count: int
    academicDone: bool
    careerActive: bool


class ReadinessState(BaseModel):
    academic: float
    career: float
    confidence: Literal["low", "medium", "high"]


class TodayResponse(BaseModel):
    tasks: list[TaskItem]
    streak: StreakState
    readiness: ReadinessState


def stable_task_id(student_id: str, day: str, goal_type: str, topic: str) -> str:
    """Deterministic task ID for a roadmap-derived item — stable across
    repeated GET /tasks/today calls so POST /tasks/{id}/complete can
    address a specific task (same pattern as struggle-detector's stable
    offer IDs, item 4a).
    """
    raw = f"{student_id}|{day}|{goal_type}|{topic}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _combine_confidence(a: str, b: str) -> str:
    """The wire contract has one confidence slot covering two separate
    readiness numbers. Academic and career scores stay distinct (never
    blended); confidence takes the weaker of the two so the UI renders
    the wide-band empty state whenever either dimension is uncertain,
    rather than implying more certainty than the thinner-evidence side
    actually has.
    """
    return min((a, b), key=lambda c: _CONFIDENCE_RANK.get(c, 0))


class _StubDB:
    """In-memory fixture stand-in for Subhiksha's DB layer (task completion state)."""

    def __init__(self) -> None:
        self._TASK_STATUS: dict[str, TaskStatus] = {}
        self._TASK_META: dict[str, dict] = {}

    def get_task_status(self, task_id: str) -> TaskStatus:
        return self._TASK_STATUS.get(task_id, "default")

    def set_task_status(self, task_id: str, status: TaskStatus) -> None:
        self._TASK_STATUS[task_id] = status

    def set_task_meta(self, task_id: str, meta: dict) -> None:
        self._TASK_META[task_id] = meta

    def get_task_meta(self, task_id: str) -> dict | None:
        return self._TASK_META.get(task_id)


db = _StubDB()


def roadmap_day_to_task_item(student_id: str, day: RoadmapDay) -> TaskItem:
    """Shared conversion used by both /tasks/today and (item 9) /roadmap's
    grouped TaskItem shape, so task identity is computed exactly once.
    """
    task_id = stable_task_id(student_id, day.day, day.type, day.topic)
    status = db.get_task_status(task_id)
    db.set_task_meta(task_id, {"student_id": student_id, "goal_type": day.type, "topic": day.topic})
    return TaskItem(id=task_id, goalType=day.type, title=day.topic, reason=day.reason, status=status)


def get_today_tasks(student_id: str) -> list[TaskItem]:
    roadmap_days = generate_roadmap(student_id)
    pinned = roadmap_days[:MAX_TASKS_PER_DAY]
    return [roadmap_day_to_task_item(student_id, day) for day in pinned]


def get_today_response(student_id: str) -> TodayResponse:
    tasks = get_today_tasks(student_id)

    academic = compute_readiness(student_id, "academic")
    career = compute_readiness(student_id, "career")

    return TodayResponse(
        tasks=tasks,
        streak=StreakState(
            count=streak_db.get_streak_count(student_id),
            academicDone=streak_db.today_academic_task_completed(student_id),
            careerActive=streak_db.today_github_or_leetcode_activity(student_id),
        ),
        readiness=ReadinessState(
            academic=academic.score,
            career=career.score,
            confidence=_combine_confidence(academic.confidence, career.confidence),
        ),
    )


def complete_task(student_id: str, task_id: str) -> None:
    db.set_task_status(task_id, "done")

    meta = db.get_task_meta(task_id)
    if meta and meta.get("goal_type") == "academic":
        streak_db.mark_academic_task_completed_today(student_id)

    check_streak_increment(student_id)
