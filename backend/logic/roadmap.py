"""Roadmap Generator (Backend Spec §6, PRD §4.7).

One engine, two goal types. Academic items are backward-planned from
the nearest exam date; career items are forward-planned from the
job-role skill gap. Both share the same DAG walk from Phase 1's
dag.py (build_dag / first_unsatisfied_node) and the same output shape.

Subhiksha's DB isn't live yet, so all reads (learning profile, GitHub
activity, LeetCode submissions, exam schedule) are stubbed with
fixture data shaped like the Moodle-mirrored fields in PRD §3.4 —
swap-in-ready for a real DB later, same pattern as Phase 1's
readiness stub.
"""

from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel

from backend.logic.dag import build_dag, first_unsatisfied_node

ACADEMIC_MASTERY_THRESHOLD = 75  # avg_score at/above this counts the node as satisfied

# Nodes considered career skills rather than academic topics — used to split
# a single DAG gap-walk into the two planning tracks (§6: "same DAG walk").
CAREER_NODES = {
    "git-github",
    "leetcode-easy",
    "leetcode-medium",
    "system-design-basics",
    "resume-building",
    "mock-interviews",
}

ROLE_SKILL_WEIGHTS: dict[str, dict[str, float]] = {
    "SDE": {
        "arrays": 1.0,
        "hash-tables": 1.0,
        "dsa-graphs": 2.0,
        "dynamic-programming": 2.0,
        "leetcode-easy": 1.0,
        "leetcode-medium": 3.0,
        "system-design-basics": 2.0,
        "git-github": 1.0,
        "resume-building": 1.0,
        "mock-interviews": 2.0,
    },
    "Data": {
        "probability": 2.0,
        "statistics": 2.0,
        "sql": 2.0,
        "python-basics": 1.0,
        "leetcode-easy": 1.0,
        "git-github": 1.0,
        "resume-building": 1.0,
        "mock-interviews": 2.0,
    },
    "Core": {
        "operating-systems": 2.0,
        "computer-networks": 2.0,
        "dbms": 2.0,
        "system-design-basics": 1.0,
        "git-github": 1.0,
        "resume-building": 1.0,
        "mock-interviews": 2.0,
    },
}


class RoadmapDay(BaseModel):
    day: str  # ISO date
    type: Literal["academic", "career"]
    topic: str
    reason: str  # e.g. "exam in 18 days" or "gap vs SDE role"


class _StubDB:
    """Fixture stand-in for Subhiksha's DB layer (learning_profile, github_activity,
    leetcode_submissions, exam schedule). Keys here are already normalized to DAG
    node ids, mirroring what the LMS Connector would write after mapping course
    names to skill nodes upstream — not this layer's job.
    """

    _LEARNING_PROFILE: dict[str, dict] = {
        "student-1": {
            "dbms": {"avg_score": 81, "trend": "up", "last_test": 78},
            "oop": {"avg_score": 88, "trend": "up", "last_test": 85},
            "derivatives": {"avg_score": 62, "trend": "down", "last_test": 58},
            "attendance_pct": 84,
        },
    }

    _GITHUB_ACTIVITY: dict[str, list[dict]] = {
        "student-1": [
            {"repo": "leetcode-practice", "commits_today": 2, "last_commit": "2026-07-22T09:14:00Z"},
        ],
    }

    _LEETCODE_SUBMISSIONS: dict[str, list[dict]] = {
        "student-1": [
            {
                "problem": "Two Sum",
                "difficulty": "Easy",
                "time_taken_seconds": 540,
                "attempts": 2,
                "solved_at": "2026-07-20T10:05:00Z",
            },
        ],
    }

    _EXAM_SCHEDULE: dict[str, list[dict]] = {
        "student-1": [
            {"subject": "dbms", "exam_date": "2026-08-10"},
        ],
    }

    _INTAKE_ANSWERS: dict[str, dict[str, str]] = {
        "student-1": {"oop": "confident", "python-basics": "confident"},
    }

    _TARGET_ROLE: dict[str, str] = {
        "student-1": "SDE",
    }

    def get_learning_profile(self, student_id: str) -> dict:
        return self._LEARNING_PROFILE.get(student_id, {})

    def get_github_activity(self, student_id: str) -> list[dict]:
        return self._GITHUB_ACTIVITY.get(student_id, [])

    def get_leetcode_submissions(self, student_id: str) -> list[dict]:
        return self._LEETCODE_SUBMISSIONS.get(student_id, [])

    def get_exam_schedule(self, student_id: str) -> list[dict]:
        return self._EXAM_SCHEDULE.get(student_id, [])

    def get_intake_answers(self, student_id: str) -> dict[str, str]:
        return self._INTAKE_ANSWERS.get(student_id, {})

    def get_target_role(self, student_id: str) -> str:
        return self._TARGET_ROLE.get(student_id, "SDE")


db = _StubDB()


def compute_skill_weights(target_role: str) -> dict[str, float]:
    return ROLE_SKILL_WEIGHTS.get(target_role, {})


def compute_satisfied_nodes(
    profile: dict,
    github: list[dict],
    leetcode: list[dict],
    intake_answers: dict[str, str],
) -> set[str]:
    """Combine evidence sources into the `satisfied` set first_unsatisfied_node() expects."""
    satisfied: set[str] = set()

    for node, entry in profile.items():
        if node == "attendance_pct":
            continue
        if isinstance(entry, dict) and entry.get("avg_score", 0) >= ACADEMIC_MASTERY_THRESHOLD:
            satisfied.add(node)

    if github:
        satisfied.add("git-github")

    difficulties_solved = {s.get("difficulty") for s in leetcode}
    if "Easy" in difficulties_solved:
        satisfied.add("leetcode-easy")
    if "Medium" in difficulties_solved:
        satisfied.add("leetcode-medium")

    for node, rating in intake_answers.items():
        if rating == "confident":
            satisfied.add(node)

    return satisfied


def _split_gap_by_type(gap_nodes: list[str]) -> tuple[list[str], list[str]]:
    academic = [n for n in gap_nodes if n not in CAREER_NODES]
    career = [n for n in gap_nodes if n in CAREER_NODES]
    return academic, career


def backward_plan(gap_nodes: list[str], exam_dates: list[str]) -> list[RoadmapDay]:
    """Academic: schedule gap nodes working backward from the nearest exam date."""
    if not gap_nodes or not exam_dates:
        return []

    nearest_exam = min(date.fromisoformat(d) for d in exam_dates)
    today = date.today()
    days_until_exam = max((nearest_exam - today).days, 1)

    n = len(gap_nodes)
    step = max(days_until_exam // n, 1)

    days = []
    for i, node in enumerate(gap_nodes):
        scheduled = today + timedelta(days=i * step)
        remaining = (nearest_exam - scheduled).days
        days.append(
            RoadmapDay(
                day=scheduled.isoformat(),
                type="academic",
                topic=node,
                reason=f"exam in {remaining} days",
            )
        )
    return days


def forward_plan(gap_nodes: list[str], role_weights: dict[str, float], role: str = "career") -> list[RoadmapDay]:
    """Career: schedule gap nodes forward from today, prioritized by role-skill weight."""
    if not gap_nodes:
        return []

    ordered = sorted(gap_nodes, key=lambda n: -role_weights.get(n, 0))
    today = date.today()

    days = []
    for i, node in enumerate(ordered):
        scheduled = today + timedelta(days=i)
        days.append(
            RoadmapDay(
                day=scheduled.isoformat(),
                type="career",
                topic=node,
                reason=f"gap vs {role} role",
            )
        )
    return days


def merge_by_day(academic_days: list[RoadmapDay], career_days: list[RoadmapDay]) -> list[RoadmapDay]:
    return sorted(academic_days + career_days, key=lambda d: d.day)


def generate_roadmap(student_id: str) -> list[RoadmapDay]:
    profile = db.get_learning_profile(student_id)
    github = db.get_github_activity(student_id)
    leetcode = db.get_leetcode_submissions(student_id)
    intake_answers = db.get_intake_answers(student_id)

    satisfied = compute_satisfied_nodes(profile, github, leetcode, intake_answers)

    g = build_dag()
    gap_nodes = first_unsatisfied_node(g, satisfied)
    academic_gap, career_gap = _split_gap_by_type(gap_nodes)

    exam_dates = [e["exam_date"] for e in db.get_exam_schedule(student_id)]
    academic_days = backward_plan(academic_gap, exam_dates)

    target_role = db.get_target_role(student_id)
    role_weights = compute_skill_weights(target_role)
    career_days = forward_plan(career_gap, role_weights, role=target_role)

    return merge_by_day(academic_days, career_days)
