import pytest

from backend.logic.struggle_detector import (
    BANNED_WORDS,
    QuizScoreRecord,
    StruggleOffer,
    _assert_no_banned_words,
    check_for_struggle_signals,
    db,
    log_struggle_correction,
)


@pytest.fixture(autouse=True)
def _reset_stub_db():
    db._QUIZ_SCORES.clear()
    db._DAYS_SINCE_LAST_COMMIT.clear()
    db._EVENTS.clear()
    yield
    db._QUIZ_SCORES.clear()
    db._DAYS_SINCE_LAST_COMMIT.clear()
    db._EVENTS.clear()


def test_academic_signal_fires_on_score_dip_vs_median():
    db._QUIZ_SCORES["s1"] = [
        QuizScoreRecord(subject="derivatives", grade_pct=50.0, subject_median=80.0, missed_topics=["chain-rule"]),
    ]
    db._DAYS_SINCE_LAST_COMMIT["s1"] = 0

    offers = check_for_struggle_signals("s1")

    assert len(offers) == 1
    assert offers[0].goal_type == "academic"
    assert offers[0].topic == "chain-rule"
    assert "chain-rule" in offers[0].reason


def test_academic_signal_does_not_fire_within_threshold():
    db._QUIZ_SCORES["s2"] = [
        QuizScoreRecord(subject="oop", grade_pct=75.0, subject_median=80.0, missed_topics=["encapsulation"]),
    ]
    db._DAYS_SINCE_LAST_COMMIT["s2"] = 0

    offers = check_for_struggle_signals("s2")

    assert offers == []  # 5pt dip is within THRESHOLD (15pt)


def test_career_signal_fires_on_commit_gap_over_two_days():
    db._QUIZ_SCORES["s3"] = []
    db._DAYS_SINCE_LAST_COMMIT["s3"] = 3

    offers = check_for_struggle_signals("s3")

    assert len(offers) == 1
    assert offers[0].goal_type == "career"
    assert offers[0].topic == "current project"
    assert "2 days" in offers[0].reason


def test_career_signal_does_not_fire_at_exactly_two_days():
    db._QUIZ_SCORES["s4"] = []
    db._DAYS_SINCE_LAST_COMMIT["s4"] = 2

    offers = check_for_struggle_signals("s4")

    assert offers == []


def test_both_signals_can_fire_together():
    db._QUIZ_SCORES["s5"] = [
        QuizScoreRecord(subject="integrals", grade_pct=40.0, subject_median=70.0, missed_topics=["u-substitution"]),
    ]
    db._DAYS_SINCE_LAST_COMMIT["s5"] = 5

    offers = check_for_struggle_signals("s5")

    assert len(offers) == 2
    goal_types = {o.goal_type for o in offers}
    assert goal_types == {"academic", "career"}


def test_generated_offer_reason_never_contains_banned_words():
    db._QUIZ_SCORES["s6"] = [
        QuizScoreRecord(subject="dbms", grade_pct=30.0, subject_median=75.0, missed_topics=["normalization"]),
    ]
    db._DAYS_SINCE_LAST_COMMIT["s6"] = 10

    offers = check_for_struggle_signals("s6")

    assert offers  # sanity: signals actually fired
    for offer in offers:
        lowered = offer.reason.lower()
        for banned in BANNED_WORDS:
            assert banned not in lowered


def test_assert_no_banned_words_raises_on_banned_copy():
    with pytest.raises(AssertionError):
        _assert_no_banned_words("Looks like you're stuck on this topic")
    with pytest.raises(AssertionError):
        _assert_no_banned_words("You're struggling with derivatives")
    with pytest.raises(AssertionError):
        _assert_no_banned_words("You're falling behind on the roadmap")


def test_assert_no_banned_words_allows_coach_style_copy():
    _assert_no_banned_words("Missed 2 questions on chain-rule")
    _assert_no_banned_words("No commit in 2 days")


def test_log_struggle_correction_logs_accepted_offer():
    log_struggle_correction("offer-1", accepted=True, features={"topic": "chain-rule"})

    events = db.get_logged_events("offer-1")
    assert len(events) == 1
    assert events[0].accepted is True


def test_log_struggle_correction_logs_rejected_offer_with_equal_weight():
    log_struggle_correction("offer-2", accepted=False, features={"topic": "current project"})

    events = db.get_logged_events("offer-2")
    assert len(events) == 1
    assert events[0].accepted is False  # "not actually stuck" is logged, not discarded


def test_log_struggle_correction_both_outcomes_persist_together():
    log_struggle_correction("offer-a", accepted=True, features={})
    log_struggle_correction("offer-b", accepted=False, features={})

    all_events = db.get_logged_events()
    assert len(all_events) == 2
    accepted_flags = {e.offer_id: e.accepted for e in all_events}
    assert accepted_flags == {"offer-a": True, "offer-b": False}
