"""Streak Logic — dual-gate (Backend Spec §9, PRD §4.10).

Increments only if BOTH conditions are met the same day: an academic
task/test completed AND career activity (GitHub or LeetCode) logged.
Login alone never counts. This is the server-side source of truth
Thaariha's client optimistically predicts and reconciles against, so
the check must be deterministic and cause no side effect unless both
gates pass.

Subhiksha's DB isn't live yet, so today's-activity reads and the
streak counter are stubbed with an in-memory _StubDB — swap-in-ready
for a real DB later, same pattern as prior phases.
"""


class _StubDB:
    """In-memory fixture stand-in for Subhiksha's DB layer (daily task/activity log, streak counter)."""

    def __init__(self) -> None:
        self._ACADEMIC_DONE_TODAY: dict[str, bool] = {"student-1": True}
        self._CAREER_ACTIVE_TODAY: dict[str, bool] = {"student-1": True}
        self._STREAK_COUNT: dict[str, int] = {"student-1": 4}
        self._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY: dict[str, float] = {"student-1": 22.0}

    def today_academic_task_completed(self, student_id: str) -> bool:
        return self._ACADEMIC_DONE_TODAY.get(student_id, False)

    def today_github_or_leetcode_activity(self, student_id: str) -> bool:
        return self._CAREER_ACTIVE_TODAY.get(student_id, False)

    def increment_streak(self, student_id: str) -> None:
        self._STREAK_COUNT[student_id] = self._STREAK_COUNT.get(student_id, 0) + 1

    def get_streak_count(self, student_id: str) -> int:
        return self._STREAK_COUNT.get(student_id, 0)

    def hours_since_last_qualifying_activity(self, student_id: str) -> float:
        """Hours since the student last logged a streak-qualifying (academic or career) action.

        Used by the streak-at-risk notification trigger (§4.17) — kept here rather
        than in notifications.py since it's genuinely part of the streak domain.
        """
        return self._HOURS_SINCE_LAST_QUALIFYING_ACTIVITY.get(student_id, 0.0)


db = _StubDB()


def check_streak_increment(student_id: str) -> bool:
    academic_done = db.today_academic_task_completed(student_id)
    career_active = db.today_github_or_leetcode_activity(student_id)
    if academic_done and career_active:
        db.increment_streak(student_id)
        return True
    return False
