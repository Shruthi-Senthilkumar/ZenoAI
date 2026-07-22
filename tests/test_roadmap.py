from datetime import date, timedelta

from backend.logic.roadmap import (
    RoadmapDay,
    backward_plan,
    compute_satisfied_nodes,
    forward_plan,
    generate_roadmap,
    merge_by_day,
)


def test_compute_satisfied_nodes_combines_all_evidence_sources():
    profile = {
        "dbms": {"avg_score": 81},
        "derivatives": {"avg_score": 60},  # below threshold, not satisfied
        "attendance_pct": 84,  # not a skill node, must be excluded
    }
    github = [{"repo": "x", "commits_today": 1}]
    leetcode = [{"problem": "Two Sum", "difficulty": "Easy"}]
    intake_answers = {"oop": "confident", "python-basics": "used it"}

    satisfied = compute_satisfied_nodes(profile, github, leetcode, intake_answers)

    assert satisfied == {"dbms", "git-github", "leetcode-easy", "oop"}
    assert "derivatives" not in satisfied
    assert "attendance_pct" not in satisfied
    assert "python-basics" not in satisfied  # "used it" is not "confident"


def test_generate_roadmap_excludes_satisfied_nodes_from_gaps():
    days = generate_roadmap("student-1")
    topics = {d.topic for d in days}
    # student-1's fixture evidence satisfies these; they must never be scheduled
    assert "dbms" not in topics
    assert "oop" not in topics
    assert "python-basics" not in topics
    assert "git-github" not in topics
    assert "leetcode-easy" not in topics


def test_generate_roadmap_returns_roadmap_day_objects_for_unknown_student():
    # unknown student -> empty evidence -> no exam dates -> academic side empty,
    # but should never crash, and career side still walks the full DAG.
    days = generate_roadmap("no-such-student")
    assert all(isinstance(d, RoadmapDay) for d in days)
    assert all(d.type == "career" for d in days)  # no exam_dates -> backward_plan is []


def test_backward_plan_schedules_toward_nearest_exam_and_reports_days_remaining():
    exam_date = (date.today() + timedelta(days=10)).isoformat()
    gap_nodes = ["limits", "derivatives", "integrals"]

    days = backward_plan(gap_nodes, [exam_date])

    assert len(days) == 3
    assert all(d.type == "academic" for d in days)
    assert [d.topic for d in days] == gap_nodes
    # scheduled days must be non-decreasing and land on/before the exam
    scheduled_dates = [date.fromisoformat(d.day) for d in days]
    assert scheduled_dates == sorted(scheduled_dates)
    assert all(d <= date.fromisoformat(exam_date) for d in scheduled_dates)
    assert all("exam in" in d.reason for d in days)


def test_backward_plan_empty_without_gaps_or_exam_dates():
    assert backward_plan([], ["2026-08-10"]) == []
    assert backward_plan(["limits"], []) == []


def test_forward_plan_prioritizes_by_role_weight_descending():
    gap_nodes = ["git-github", "leetcode-medium", "resume-building"]
    role_weights = {"git-github": 1.0, "leetcode-medium": 3.0, "resume-building": 1.0}

    days = forward_plan(gap_nodes, role_weights, role="SDE")

    assert [d.topic for d in days][0] == "leetcode-medium"  # highest weight scheduled first
    assert all(d.type == "career" for d in days)
    assert all("gap vs SDE role" in d.reason for d in days)
    # scheduled starting today, one node per day, strictly increasing
    scheduled_dates = [date.fromisoformat(d.day) for d in days]
    assert scheduled_dates == sorted(set(scheduled_dates))
    assert scheduled_dates[0] == date.today()


def test_merge_by_day_interleaves_academic_and_career_chronologically():
    today = date.today()
    academic = [
        RoadmapDay(day=today.isoformat(), type="academic", topic="limits", reason="exam in 5 days"),
        RoadmapDay(
            day=(today + timedelta(days=2)).isoformat(),
            type="academic",
            topic="derivatives",
            reason="exam in 3 days",
        ),
    ]
    career = [
        RoadmapDay(
            day=(today + timedelta(days=1)).isoformat(),
            type="career",
            topic="git-github",
            reason="gap vs SDE role",
        ),
    ]

    merged = merge_by_day(academic, career)

    assert [d.day for d in merged] == sorted(d.day for d in academic + career)
    assert [(d.day, d.type) for d in merged] == [
        (today.isoformat(), "academic"),
        ((today + timedelta(days=1)).isoformat(), "career"),
        ((today + timedelta(days=2)).isoformat(), "academic"),
    ]
