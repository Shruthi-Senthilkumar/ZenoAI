import pytest

from backend.logic.streak import check_streak_increment, db


@pytest.fixture(autouse=True)
def _reset_stub_db():
    db._ACADEMIC_DONE_TODAY.clear()
    db._CAREER_ACTIVE_TODAY.clear()
    db._STREAK_COUNT.clear()
    yield
    db._ACADEMIC_DONE_TODAY.clear()
    db._CAREER_ACTIVE_TODAY.clear()
    db._STREAK_COUNT.clear()


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


def test_is_deterministic_across_repeated_calls_with_same_state():
    db._ACADEMIC_DONE_TODAY["s5"] = True
    db._CAREER_ACTIVE_TODAY["s5"] = True
    db._STREAK_COUNT["s5"] = 0

    first = check_streak_increment("s5")
    second = check_streak_increment("s5")

    assert first is True
    assert second is True
    assert db.get_streak_count("s5") == 2  # each call is a distinct day's check in this stub
