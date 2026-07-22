import pytest

from backend.logic.readiness import (
    EVIDENCE_CREDIT,
    HIGH_EVIDENCE,
    MIN_EVIDENCE,
    ReadinessResult,
    compute_readiness,
    db,
    total_evidence_volume,
)


@pytest.fixture
def _fixture_student():
    """Register/deregister a scratch student in the shared class-level fixture
    dicts without touching student-1's canonical hand-computed fixture.
    """
    student_id = "student-high-confidence"

    def _register(evidence: dict[str, str], weights: dict[str, float]):
        db._EVIDENCE.setdefault(student_id, {})["academic"] = evidence
        db._WEIGHTS.setdefault(student_id, {})["academic"] = weights
        return student_id

    yield _register
    db._EVIDENCE.pop(student_id, None)
    db._WEIGHTS.pop(student_id, None)


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


def test_confidence_graduates_to_high_at_or_above_high_evidence_threshold(_fixture_student):
    # item 9 regression: confidence used to cap out at "medium" — the
    # frontend store types confidence as "low"|"medium"|"high".
    evidence = {f"skill-{i}": "shipped" for i in range(HIGH_EVIDENCE)}
    weights = {f"skill-{i}": 1.0 for i in range(HIGH_EVIDENCE)}
    student_id = _fixture_student(evidence, weights)

    result = compute_readiness(student_id, "academic")

    assert result.confidence == "high"


def test_confidence_stays_medium_just_below_high_evidence_threshold(_fixture_student):
    evidence = {f"skill-{i}": "shipped" for i in range(HIGH_EVIDENCE - 1)}
    weights = {f"skill-{i}": 1.0 for i in range(HIGH_EVIDENCE - 1)}
    student_id = _fixture_student(evidence, weights)

    result = compute_readiness(student_id, "academic")

    assert result.confidence == "medium"


def test_confidence_literal_accepts_high():
    # a bare construction proves "high" is a valid literal, not just reachable
    result = ReadinessResult(score=0.9, confidence="high")
    assert result.confidence == "high"
