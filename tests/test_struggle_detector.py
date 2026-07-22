import pytest

from backend.logic.struggle_detector import (
    BANNED_WORDS,
    SAFE_FALLBACK_REASON,
    BannedCopyError,
    QuizScoreRecord,
    StruggleOffer,
    _assert_no_banned_words,
    _make_offer,
    check_for_struggle_signals,
    db,
    log_struggle_correction,
)


@pytest.fixture(autouse=True)
def _reset_stub_db():
    db._QUIZ_SCORES.clear()
    db._DAYS_SINCE_LAST_COMMIT.clear()
    db._OFFERS.clear()
    db._OFFER_FEATURES.clear()
    db._EVENTS.clear()
    yield
    db._QUIZ_SCORES.clear()
    db._DAYS_SINCE_LAST_COMMIT.clear()
    db._OFFERS.clear()
    db._OFFER_FEATURES.clear()
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
    assert "3 days" in offers[0].reason


def test_career_reason_reflects_the_actual_measured_gap_not_a_hardcoded_number():
    # item 4d regression: the copy used to hardcode "No commit in 2 days"
    # regardless of the real gap. The old code would pass a naive
    # "2 days" in reason check even at a 5-day gap — assert the real
    # number appears and the stale hardcoded one doesn't.
    db._QUIZ_SCORES["s3b"] = []
    db._DAYS_SINCE_LAST_COMMIT["s3b"] = 5

    offers = check_for_struggle_signals("s3b")

    assert "5 days" in offers[0].reason
    assert "No commit in 2 days" not in offers[0].reason


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


def test_assert_no_banned_words_raises_typed_exception_not_bare_assert():
    # item 4c regression: a bare `assert` is stripped under python -O and
    # would surface as an unhandled 500 in a route if it ever fired.
    with pytest.raises(BannedCopyError):
        _assert_no_banned_words("Looks like you're stuck on this topic")
    with pytest.raises(BannedCopyError):
        _assert_no_banned_words("You're struggling with derivatives")
    with pytest.raises(BannedCopyError):
        _assert_no_banned_words("You're falling behind on the roadmap")


def test_make_offer_falls_back_to_safe_copy_instead_of_raising():
    # item 4c: _make_offer must catch BannedCopyError and substitute safe
    # generic copy rather than letting the exception propagate.
    offer = _make_offer(
        student_id="s-banned",
        goal_type="academic",
        topic="derivatives",
        reason="You're falling behind on derivatives",
        features={},
        signal_window="2026-07-22",
    )
    assert offer.reason == SAFE_FALLBACK_REASON
    for banned in BANNED_WORDS:
        assert banned not in offer.reason.lower()


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


def test_offer_ids_are_stable_across_repeated_gets():
    # item 4a regression: offer_id used to be a fresh uuid4() every call, so
    # two consecutive GETs returned different IDs and a POST /respond
    # against an earlier ID referenced nothing.
    db._QUIZ_SCORES["s7"] = [
        QuizScoreRecord(subject="derivatives", grade_pct=50.0, subject_median=80.0, missed_topics=["chain-rule"]),
    ]
    db._DAYS_SINCE_LAST_COMMIT["s7"] = 5

    first_call = check_for_struggle_signals("s7")
    second_call = check_for_struggle_signals("s7")

    first_ids = {o.offer_id for o in first_call}
    second_ids = {o.offer_id for o in second_call}
    assert first_ids == second_ids
    assert len(first_ids) == 2  # both signals fired, both stable


def test_repeated_get_offer_id_can_be_used_to_respond():
    db._QUIZ_SCORES["s8"] = []
    db._DAYS_SINCE_LAST_COMMIT["s8"] = 4

    offers = check_for_struggle_signals("s8")
    offer_id = offers[0].offer_id

    # a second GET must still resolve the same offer_id in the stub
    check_for_struggle_signals("s8")
    assert db.get_offer(offer_id) is not None


def test_log_struggle_correction_uses_server_captured_features_not_client_supplied():
    # item 4b regression: features used to come straight from whatever the
    # client POSTed. Now they're captured server-side at offer-generation
    # time and any client-supplied features are ignored.
    db._QUIZ_SCORES["s9"] = [
        QuizScoreRecord(subject="dbms", grade_pct=30.0, subject_median=75.0, missed_topics=["normalization"]),
    ]
    db._DAYS_SINCE_LAST_COMMIT["s9"] = 0

    offers = check_for_struggle_signals("s9")
    offer_id = offers[0].offer_id

    log_struggle_correction(offer_id, accepted=True, features={"fabricated": "client-supplied nonsense"})

    events = db.get_logged_events(offer_id)
    assert len(events) == 1
    assert "fabricated" not in events[0].features
    assert events[0].features == db.get_offer_features(offer_id)
    assert events[0].features["subject"] == "dbms"
    assert events[0].features["missed_topics"] == ["normalization"]


def test_log_struggle_correction_unknown_offer_id_gets_empty_features_not_a_crash():
    log_struggle_correction("never-generated-offer", accepted=False, features={"whatever": True})

    events = db.get_logged_events("never-generated-offer")
    assert events[0].features == {}
