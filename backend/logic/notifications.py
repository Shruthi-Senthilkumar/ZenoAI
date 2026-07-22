"""In-App Notification Banner logic (PRD §4.17, UI/UX Spec §4.10).

Checks trigger signals in priority order — streak-at-risk >
resume-bullet-ready > reminder — and returns the single
highest-priority active banner, or None. Max one banner at a time.

Reuses Phase 3's streak stub (streak count + hours-since-last-activity)
and struggle-detector's career signal (commit gap) rather than
re-implementing those checks; only genuinely new signals
(resume-bullet-ready, assignment-due) are stubbed here.
"""

from backend.logic.streak import db as streak_db
from backend.logic.struggle_detector import check_for_struggle_signals
from backend.schemas.notification import NotificationBanner

STREAK_AT_RISK_HOURS = 20


class _StubDB:
    """Fixture stand-in for signals not modeled elsewhere yet (resume bullet status, assignment due dates)."""

    _RESUME_BULLET_READY: dict[str, bool] = {"student-1": False}
    _ASSIGNMENT_DUE_TOMORROW: dict[str, bool] = {"student-1": True}

    def has_unseen_resume_bullet(self, student_id: str) -> bool:
        return self._RESUME_BULLET_READY.get(student_id, False)

    def mark_resume_bullet_ready(self, student_id: str) -> None:
        """Set by resume.py on successful generation (item 2, master prompt)."""
        self._RESUME_BULLET_READY[student_id] = True

    def clear_resume_bullet_ready(self, student_id: str) -> None:
        """Cleared once the banner has actually been surfaced — 'unseen' stops
        being true the moment the student has seen it."""
        self._RESUME_BULLET_READY[student_id] = False

    def has_assignment_due_tomorrow(self, student_id: str) -> bool:
        return self._ASSIGNMENT_DUE_TOMORROW.get(student_id, False)


db = _StubDB()


def _check_streak_at_risk(student_id: str) -> NotificationBanner | None:
    streak = streak_db.get_streak_count(student_id)
    hours = streak_db.hours_since_last_qualifying_activity(student_id)
    if streak > 0 and hours > STREAK_AT_RISK_HOURS:
        return NotificationBanner(
            type="streak-at-risk",
            message=f"Your {streak}-day streak is at risk — keep it going today!",
            priority=1,
        )
    return None


def _check_resume_bullet_ready(student_id: str) -> NotificationBanner | None:
    if db.has_unseen_resume_bullet(student_id):
        db.clear_resume_bullet_ready(student_id)  # surfaced now -> no longer "unseen"
        return NotificationBanner(
            type="resume-bullet-ready",
            message="A new resume bullet is ready to review.",
            priority=2,
        )
    return None


def _check_reminder(student_id: str) -> NotificationBanner | None:
    if db.has_assignment_due_tomorrow(student_id):
        return NotificationBanner(type="reminder", message="Assignment due tomorrow", priority=3)

    # Reuse struggle-detector's career signal (commit gap) instead of
    # re-implementing its threshold here — just reformat as a notification.
    for offer in check_for_struggle_signals(student_id):
        if offer.goal_type == "career":
            return NotificationBanner(type="reminder", message=offer.reason, priority=3)

    return None


def get_active_notification(student_id: str) -> NotificationBanner | None:
    for check in (_check_streak_at_risk, _check_resume_bullet_ready, _check_reminder):
        banner = check(student_id)
        if banner is not None:
            return banner
    return None
