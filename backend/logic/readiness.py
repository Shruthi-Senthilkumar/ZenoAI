"""Readiness Score formula (Backend Spec §11, PRD §7).

Weighted-coverage formula over per-skill evidence levels. Academic and
Career Readiness are computed separately per goal type and never
blended into a single number (PRD §7) — `compute_readiness` takes
`goal_type` as a parameter precisely so callers can never average them.

Subhiksha's DB layer isn't live yet, so `db.get_evidence_levels()` and
`db.get_skill_weights()` are stubbed with hardcoded fixture dicts here
so the formula is provably correct against known inputs.
"""

from typing import Literal

from pydantic import BaseModel

EVIDENCE_CREDIT = {"none": 0.0, "practiced": 0.4, "applied": 0.7, "shipped": 1.0}

MIN_EVIDENCE = 3  # minimum number of scored skills before confidence graduates past "low"

GoalType = Literal["academic", "career"]


class ReadinessResult(BaseModel):
    score: float
    confidence: Literal["low", "medium"]


class _StubDB:
    """Fixture stand-in for Subhiksha's DB layer (learning_profile / skill_weights)."""

    _EVIDENCE: dict[str, dict[GoalType, dict[str, str]]] = {
        "student-1": {
            "academic": {
                "limits": "shipped",
                "derivatives": "applied",
                "integrals": "practiced",
                "arrays": "shipped",
            },
            "career": {
                "git-github": "shipped",
                "leetcode-easy": "applied",
            },
        },
    }

    _WEIGHTS: dict[str, dict[GoalType, dict[str, float]]] = {
        "student-1": {
            "academic": {
                "limits": 1.0,
                "derivatives": 2.0,
                "integrals": 2.0,
                "arrays": 1.0,
            },
            "career": {
                "git-github": 1.0,
                "leetcode-easy": 3.0,
            },
        },
    }

    def get_evidence_levels(self, student_id: str, goal_type: GoalType) -> dict[str, str]:
        return self._EVIDENCE.get(student_id, {}).get(goal_type, {})

    def get_skill_weights(self, student_id: str, goal_type: GoalType) -> dict[str, float]:
        return self._WEIGHTS.get(student_id, {}).get(goal_type, {})


db = _StubDB()


def total_evidence_volume(evidence: dict[str, str]) -> int:
    """Count of skills with any recorded evidence (not 'none')."""
    return sum(1 for level in evidence.values() if level != "none")


def compute_readiness(student_id: str, goal_type: GoalType) -> ReadinessResult:
    evidence = db.get_evidence_levels(student_id, goal_type)  # none/practiced/applied/shipped
    weights = db.get_skill_weights(student_id, goal_type)  # exam syllabus or job-role weight

    numerator = sum(
        weights[s] * EVIDENCE_CREDIT[evidence.get(s, "none")] for s in weights
    )
    denominator = sum(weights.values())
    score = numerator / denominator if denominator else 0

    confidence = "low" if total_evidence_volume(evidence) < MIN_EVIDENCE else "medium"
    return ReadinessResult(score=score, confidence=confidence)
