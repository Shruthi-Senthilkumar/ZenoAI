import pytest

from backend.logic.streak import check_streak_increment, db


@pytest.fixture(autouse=True)
def _reset_stub_db():
    db._ACADEMIC_DONE_TODAY.clear()
    db._CAREER_ACTIVE_TODAY.clear()
    db._STREAK_COUNT.clear()
    db._LAST_INCREMENTED_DATE.clear()
    yield
    db._ACADEMIC_DONE_TODAY.clear()
    db._CAREER_ACTIVE_TODAY.clear()
    db._STREAK_COUNT.clear()
    db._LAST_INCREMENTED_DATE.clear()


def test_increments_when_both_conditions_met():
    db._ACADEMIC_DONE_TODAY["s1"] = True
    db._CAREER_ACTIVE_TODAY["s1"] = True
    db._STREAK_COUNT["s1"] = 0

    result = check_streak_increment("s1")

    assert result is True
    assert db.get_streak_count("s1") == 1


def test_does_not_increment_when_only_academic_done():
    db._ACADEMIC_DONE_TODAY["s2"] = True
    db._CAREER_ACTIVE_TODAY["s2"] = False
    db._STREAK_COUNT["s2"] = 3

    result = check_streak_increment("s2")

    assert result is False
    assert db.get_streak_count("s2") == 3  # unchanged, no partial state


def test_does_not_increment_when_only_career_active():
    db._ACADEMIC_DONE_TODAY["s3"] = False
    db._CAREER_ACTIVE_TODAY["s3"] = True
    db._STREAK_COUNT["s3"] = 3

    result = check_streak_increment("s3")

    assert result is False
    assert db.get_streak_count("s3") == 3


def test_login_alone_never_counts_neither_condition_met():
    db._ACADEMIC_DONE_TODAY["s4"] = False
    db._CAREER_ACTIVE_TODAY["s4"] = False
    db._STREAK_COUNT["s4"] = 5

    result = check_streak_increment("s4")

    assert result is False
    assert db.get_streak_count("s4") == 5


def test_unknown_student_defaults_to_false_gates_and_no_increment():
    result = check_streak_increment("never-seen-student")

    assert result is False
    assert db.get_streak_count("never-seen-student") == 0


def test_is_idempotent_across_repeated_calls_the_same_day():
    # item 3 regression: three consecutive calls used to take a student's
    # streak from 4 to 7 (double/triple counting) because there was no
    # per-day guard. The client optimistically increments and reconciles
    # against this value on every sync, so repeated same-day calls are the
    # normal path, not an edge case — only the first should count.
    db._ACADEMIC_DONE_TODAY["s5"] = True
    db._CAREER_ACTIVE_TODAY["s5"] = True
    db._STREAK_COUNT["s5"] = 4

    first = check_streak_increment("s5")
    second = check_streak_increment("s5")
    third = check_streak_increment("s5")

    assert first is True
    assert second is False
    assert third is False
    assert db.get_streak_count("s5") == 5  # incremented exactly once, not three times


def test_no_op_guard_does_not_re_evaluate_gates_once_incremented_today():
    db._ACADEMIC_DONE_TODAY["s6"] = True
    db._CAREER_ACTIVE_TODAY["s6"] = True
    db._STREAK_COUNT["s6"] = 0

    assert check_streak_increment("s6") is True

    # even if a gate flips off after the fact, the already-incremented
    # no-op guard means the function stays a no-op today, not a rollback
    db._ACADEMIC_DONE_TODAY["s6"] = False

    assert check_streak_increment("s6") is False
    assert db.get_streak_count("s6") == 1
