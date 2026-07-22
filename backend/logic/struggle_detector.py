"""Struggle-Detector Stage A — data-collection mode only (Backend Spec §10, PRD §4.11, §2.5.6).

No composite scoring here — Stage B/C are post-hackathon and out of
scope for this build.

Critical copy rule: generated offer `reason` text must NEVER contain
"stuck," "struggling," or "behind" — coach-not-judge register,
enforced here at generation time (not just in the UI layer).

`log_struggle_correction` logs every flag — correct or not — with
equal weight. This is the labeled ground-truth dataset the PRD's
Stage A→B gate depends on (≥50 events across ≥5 users before any
scoring is trusted); "not actually stuck" responses are never
discarded.

Subhiksha's DB isn't live yet, so quiz-score history, commit recency,
and event storage are stubbed with an in-memory _StubDB — swap-in-ready
for a real DB later, same pattern as prior phases.
"""

import uuid
from typing import Literal

from pydantic import BaseModel

THRESHOLD = 15.0  # percentage points below subject median that counts as a dip

BANNED_WORDS = {"stuck", "struggling", "behind"}


class StruggleOffer(BaseModel):
    offer_id: str
    topic: str
    goal_type: Literal["academic", "career"]
    reason: str


class StruggleEvent(BaseModel):
    offer_id: str
    accepted: bool
    features: dict


class QuizScoreRecord(BaseModel):
    subject: str
    grade_pct: float
    subject_median: float
    missed_topics: list[str]


def _assert_no_banned_words(reason: str) -> None:
    lowered = reason.lower()
    for word in BANNED_WORDS:
        assert word not in lowered, f"struggle-offer reason contains banned word {word!r}: {reason!r}"


def _make_offer(topic: str, goal_type: Literal["academic", "career"], reason: str) -> StruggleOffer:
    _assert_no_banned_words(reason)
    return StruggleOffer(offer_id=str(uuid.uuid4()), topic=topic, goal_type=goal_type, reason=reason)


class _StubDB:
    """In-memory fixture stand-in for Subhiksha's DB layer (quiz_scores, github_activity, struggle_events)."""

    def __init__(self) -> None:
        self._QUIZ_SCORES: dict[str, list[QuizScoreRecord]] = {
            "student-1": [
                QuizScoreRecord(
                    subject="derivatives",
                    grade_pct=55.0,
                    subject_median=78.0,
                    missed_topics=["chain-rule", "product-rule"],
                ),
                QuizScoreRecord(
                    subject="oop",
                    grade_pct=82.0,
                    subject_median=80.0,
                    missed_topics=[],
                ),
            ],
        }
        self._DAYS_SINCE_LAST_COMMIT: dict[str, int] = {"student-1": 4}
        self._EVENTS: list[StruggleEvent] = []

    def get_recent_quiz_scores(self, student_id: str) -> list[QuizScoreRecord]:
        return self._QUIZ_SCORES.get(student_id, [])

    def days_since_last_commit(self, student_id: str) -> int:
        return self._DAYS_SINCE_LAST_COMMIT.get(student_id, 0)

    def insert(self, event: StruggleEvent) -> None:
        self._EVENTS.append(event)

    def get_logged_events(self, offer_id: str | None = None) -> list[StruggleEvent]:
        if offer_id is None:
            return list(self._EVENTS)
        return [e for e in self._EVENTS if e.offer_id == offer_id]


db = _StubDB()


def check_for_struggle_signals(student_id: str) -> list[StruggleOffer]:
    offers: list[StruggleOffer] = []

    # academic signal: quiz score dip vs. historical median, per-question detail from Moodle shape
    for q in db.get_recent_quiz_scores(student_id):
        if q.grade_pct < q.subject_median - THRESHOLD and q.missed_topics:
            offers.append(
                _make_offer(
                    topic=q.missed_topics[0],
                    goal_type="academic",
                    reason=f"Missed {len(q.missed_topics)} questions on {q.missed_topics[0]}",
                )
            )

    # career signal: commit gap (simple heuristic, Stage A only)
    if db.days_since_last_commit(student_id) > 2:
        offers.append(
            _make_offer(
                topic="current project",
                goal_type="career",
                reason="No commit in 2 days",
            )
        )

    return offers


def log_struggle_correction(offer_id: str, accepted: bool, features: dict) -> None:
    db.insert(StruggleEvent(offer_id=offer_id, accepted=accepted, features=features))
