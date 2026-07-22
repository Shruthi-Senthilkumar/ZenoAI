"""GET /dashboard/{student_id} (docs/BACKEND_SPEC_ADDENDUM.md §13, PRD §4.13).

Note: previously cited as "Backend Spec §11" — that's the readiness
formula's section number, not a Dashboard section (none existed). See
the addendum for the section this route actually belongs to.

Wires Phase 1's compute_readiness() — academic and career, always
computed separately and never blended — into the Dashboard's API
Contract shape. Subject/activity trend history is stubbed since
Subhiksha's DB isn't live yet; current streak count is pulled from
Phase 3's streak stub (backend.logic.streak).

Empty-state rule (UI/UX Spec §6): a student with zero evidence must
never see a bare 0% — the existing confidence="low" signal from
Phase 1's formula is enough for the frontend to render the
wide-confidence-band empty state. No separate empty-state field is
invented here.
"""

from fastapi import APIRouter

from backend.logic.readiness import compute_readiness
from backend.logic.streak import db as streak_db

router = APIRouter()


class _StubDB:
    """Fixture stand-in for per-subject and career trend history (Subhiksha's DB isn't live yet)."""

    _SUBJECT_TRENDS: dict[str, dict[str, list[float]]] = {
        "student-1": {"Physics": [78, 71, 62], "DBMS": [75, 81]},
    }

    _CAREER_ACTIVITY_TREND: dict[str, list[float]] = {
        "student-1": [0.40, 0.48, 0.54],
    }

    def get_subject_trends(self, student_id: str) -> dict[str, list[float]]:
        return self._SUBJECT_TRENDS.get(student_id, {})

    def get_career_activity_trend(self, student_id: str) -> list[float]:
        return self._CAREER_ACTIVITY_TREND.get(student_id, [])


db = _StubDB()


@router.get("/dashboard/{student_id}")
def get_dashboard(student_id: str) -> dict:
    academic = compute_readiness(student_id, "academic")
    career = compute_readiness(student_id, "career")

    return {
        "academic": {
            "readiness": academic.score,
            "confidence": academic.confidence,
            "subjects": db.get_subject_trends(student_id),
        },
        "career": {
            "readiness": career.score,
            "confidence": career.confidence,
            "activity_trend": db.get_career_activity_trend(student_id),
            "streak": streak_db.get_streak_count(student_id),
        },
    }
