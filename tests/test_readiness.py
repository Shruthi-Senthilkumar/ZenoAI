import pytest

from backend.logic.readiness import (
    EVIDENCE_CREDIT,
    MIN_EVIDENCE,
    ReadinessResult,
    compute_readiness,
    total_evidence_volume,
)


def test_academic_readiness_matches_hand_computed_fixture():
    # student-1 academic: weights {limits:1, derivatives:2, integrals:2, arrays:1} = 6.0
    # evidence: limits=shipped(1.0), derivatives=applied(0.7), integrals=practiced(0.4), arrays=shipped(1.0)
    # numerator = 1*1.0 + 2*0.7 + 2*0.4 + 1*1.0 = 4.2 -> score = 4.2/6.0 = 0.7
    result = compute_readiness("student-1", "academic")
    assert isinstance(result, ReadinessResult)
    assert result.score == pytest.approx(0.7)
    assert result.confidence == "medium"  # 4 scored skills >= MIN_EVIDENCE


def test_career_readiness_matches_hand_computed_fixture_and_is_low_confidence():
    # student-1 career: weights {git-github:1, leetcode-easy:3} = 4.0
    # evidence: git-github=shipped(1.0), leetcode-easy=applied(0.7)
    # numerator = 1*1.0 + 3*0.7 = 3.1 -> score = 3.1/4.0 = 0.775
    result = compute_readiness("student-1", "career")
    assert result.score == pytest.approx(0.775)
    assert result.confidence == "low"  # only 2 scored skills < MIN_EVIDENCE (3)


def test_academic_and_career_are_never_blended():
    academic = compute_readiness("student-1", "academic")
    career = compute_readiness("student-1", "career")
    assert academic.score != career.score


def test_unknown_student_yields_zero_score_and_low_confidence():
    result = compute_readiness("no-such-student", "academic")
    assert result.score == 0
    assert result.confidence == "low"


def test_evidence_credit_table_is_exact():
    assert EVIDENCE_CREDIT == {"none": 0.0, "practiced": 0.4, "applied": 0.7, "shipped": 1.0}


def test_total_evidence_volume_excludes_none():
    evidence = {"a": "none", "b": "practiced", "c": "shipped"}
    assert total_evidence_volume(evidence) == 2
    assert MIN_EVIDENCE == 3
