"""Struggle-Detector Stage A — data-collection mode only (Backend Spec §10, PRD §4.11, §2.5.6).

No composite scoring here — Stage B/C are post-hackathon and out of
scope for this build.

Critical copy rule: generated offer `reason` text must NEVER contain
"stuck," "struggling," or "behind" — coach-not-judge register,
enforced here at generation time (not just in the UI layer). The
check raises a typed BannedCopyError rather than a bare `assert`
(stripped under `python -O`, and would otherwise surface as an
unhandled 500 in a route) — `_make_offer` catches it and falls back
to a safe generic coach-copy reason instead of ever returning banned
copy or crashing.

`log_struggle_correction` logs every flag — correct or not — with
equal weight. This is the labeled ground-truth dataset the PRD's
Stage A→B gate depends on (≥50 events across ≥5 users before any
scoring is trusted); "not actually stuck" responses are never
discarded. Triggering features are captured server-side at
offer-generation time and attached from the stored offer when a
correction is logged — client-supplied features are never trusted,
so labels can't be joined to fabricated features.

Offer IDs are derived deterministically from
(student_id, goal_type, topic, signal_window) rather than minted
fresh per call, so a repeated GET /struggle/offers returns the same
IDs an earlier POST /respond can still reference. `signal_window` is
today's date — a signal that's still active tomorrow gets a fresh ID,
so Stage A doesn't file two different days' occurrences under a
single ever-growing offer record.

Subhiksha's DB isn't live yet, so quiz-score history, commit recency,
and event/offer storage are stubbed with an in-memory _StubDB —
swap-in-ready for a real DB later, same pattern as prior phases.
"""

import hashlib
from datetime import date
from typing import Literal

from pydantic import BaseModel

THRESHOLD = 15.0  # percentage points below subject median that counts as a dip

BANNED_WORDS = {"stuck", "struggling", "behind"}

SAFE_FALLBACK_REASON = "Here's something worth a quick look"


class BannedCopyError(Exception):
    """Raised when generated struggle-offer copy contains a banned word."""


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
        if word in lowered:
            raise BannedCopyError(f"struggle-offer reason contains banned word {word!r}: {reason!r}")


def _stable_offer_id(student_id: str, goal_type: str, topic: str, signal_window: str) -> str:
    raw = f"{student_id}|{goal_type}|{topic}|{signal_window}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _make_offer(
    student_id: str,
    goal_type: Literal["academic", "career"],
    topic: str,
    reason: str,
    features: dict,
    signal_window: str,
) -> StruggleOffer:
    try:
        _assert_no_banned_words(reason)
    except BannedCopyError:
        reason = SAFE_FALLBACK_REASON

    offer_id = _stable_offer_id(student_id, goal_type, topic, signal_window)
    offer = StruggleOffer(offer_id=offer_id, topic=topic, goal_type=goal_type, reason=reason)
    db.store_offer(offer, features)
    return offer


class _StubDB:
    """In-memory fixture stand-in for Subhiksha's DB layer (quiz_scores, github_activity, struggle_offers, struggle_events)."""

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
        self._OFFERS: dict[str, StruggleOffer] = {}
        self._OFFER_FEATURES: dict[str, dict] = {}
        self._EVENTS: list[StruggleEvent] = []

    def get_recent_quiz_scores(self, student_id: str) -> list[QuizScoreRecord]:
        return self._QUIZ_SCORES.get(student_id, [])

    def days_since_last_commit(self, student_id: str) -> int:
        return self._DAYS_SINCE_LAST_COMMIT.get(student_id, 0)

    def store_offer(self, offer: StruggleOffer, features: dict) -> None:
        self._OFFERS[offer.offer_id] = offer
        self._OFFER_FEATURES[offer.offer_id] = features

    def get_offer(self, offer_id: str) -> StruggleOffer | None:
        return self._OFFERS.get(offer_id)

    def get_offer_features(self, offer_id: str) -> dict:
        return self._OFFER_FEATURES.get(offer_id, {})

    def insert(self, event: StruggleEvent) -> None:
        self._EVENTS.append(event)

    def get_logged_events(self, offer_id: str | None = None) -> list[StruggleEvent]:
        if offer_id is None:
            return list(self._EVENTS)
        return [e for e in self._EVENTS if e.offer_id == offer_id]


db = _StubDB()


def check_for_struggle_signals(student_id: str) -> list[StruggleOffer]:
    offers: list[StruggleOffer] = []
    signal_window = date.today().isoformat()

    # academic signal: quiz score dip vs. historical median, per-question detail from Moodle shape
    for q in db.get_recent_quiz_scores(student_id):
        if q.grade_pct < q.subject_median - THRESHOLD and q.missed_topics:
            offers.append(
                _make_offer(
                    student_id=student_id,
                    goal_type="academic",
                    topic=q.missed_topics[0],
                    reason=f"Missed {len(q.missed_topics)} questions on {q.missed_topics[0]}",
                    features={
                        "subject": q.subject,
                        "grade_pct": q.grade_pct,
                        "subject_median": q.subject_median,
                        "missed_topics": q.missed_topics,
                    },
                    signal_window=signal_window,
                )
            )

    # career signal: commit gap (simple heuristic, Stage A only)
    days_since_commit = db.days_since_last_commit(student_id)
    if days_since_commit > 2:
        offers.append(
            _make_offer(
                student_id=student_id,
                goal_type="career",
                topic="current project",
                reason=f"No commit in {days_since_commit} days",
                features={"days_since_last_commit": days_since_commit},
                signal_window=signal_window,
            )
        )

    return offers


def log_struggle_correction(offer_id: str, accepted: bool, features: dict | None = None) -> None:
    """Log a Stage A correction.

    `features` is accepted for call-site compatibility but ignored: the
    triggering features captured server-side at offer-generation time
    (via _make_offer/store_offer) are used instead, so a client can't
    fabricate the labeled features for the Stage A->B ground-truth
    dataset. Both accepted and rejected offers are logged with equal
    weight — "not actually stuck" is never discarded.
    """
    captured_features = db.get_offer_features(offer_id)
    db.insert(StruggleEvent(offer_id=offer_id, accepted=accepted, features=captured_features))
