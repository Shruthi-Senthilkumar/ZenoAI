from datetime import date, timedelta

from backend.logic.dag import PREREQS, build_dag
from backend.logic.roadmap import (
    ROADMAP_HORIZON_DAYS,
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
    # unknown student -> empty evidence, no exam dates -> academic side falls
    # back to forward-planning (item 2d) instead of going empty; should never
    # crash, and both goal types can appear.
    days = generate_roadmap("no-such-student")
    assert all(isinstance(d, RoadmapDay) for d in days)
    assert {d.type for d in days}.issubset({"academic", "career"})
    assert any(d.type == "academic" for d in days)  # no exam -> forward-planned fallback, not empty


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


def test_backward_plan_never_overflows_past_the_exam_when_gaps_exceed_days():
    # item 2b regression: 10 gap nodes but only 3 days until the exam used to
    # overflow past the exam date with a negative day count in `reason`.
    exam_date = (date.today() + timedelta(days=3)).isoformat()
    gap_nodes = [f"topic-{i}" for i in range(10)]

    days = backward_plan(gap_nodes, [exam_date])

    assert len(days) == 3  # truncated to what fits, not all 10
    assert gap_nodes[:3] == [d.topic for d in days]  # kept the earliest/foundational ones
    for d in days:
        assert "exam in -" not in d.reason
        remaining = int(d.reason.removeprefix("exam in ").removesuffix(" days"))
        assert remaining > 0
    scheduled_dates = [date.fromisoformat(d.day) for d in days]
    assert max(scheduled_dates) < date.fromisoformat(exam_date)  # never on/after the exam


def test_backward_plan_returns_empty_when_exam_is_today_or_past():
    exam_date = date.today().isoformat()
    assert backward_plan(["limits"], [exam_date]) == []


def test_forward_plan_prioritizes_by_role_weight_descending():
    gap_nodes = ["git-github", "leetcode-medium", "resume-building"]
    role_weights = {"git-github": 1.0, "leetcode-medium": 3.0, "resume-building": 1.0}

    days = forward_plan(gap_nodes, role_weights, role="SDE")

    # leetcode-medium has no unresolved dependency among these 3 nodes, so
    # weight alone decides it goes first; resume-building genuinely depends
    # on git-github in the DAG, so topological order still wins there.
    assert [d.topic for d in days][0] == "leetcode-medium"
    assert days.index(next(d for d in days if d.topic == "git-github")) < days.index(
        next(d for d in days if d.topic == "resume-building")
    )
    assert all(d.type == "career" for d in days)
    assert all("gap vs SDE role" in d.reason for d in days)
    # scheduled starting today, one node per day, strictly increasing
    scheduled_dates = [date.fromisoformat(d.day) for d in days]
    assert scheduled_dates == sorted(set(scheduled_dates))
    assert scheduled_dates[0] == date.today()


def test_forward_plan_never_schedules_a_node_before_its_dag_ancestors_full_career_gap():
    # item 2a regression: the full career-classified gap, not a hand-picked
    # 3-node list — mock-interviews used to schedule before its own
    # prerequisite resume-building because the old code sorted by weight
    # alone, destroying topological order.
    career_gap = [
        "git-github",
        "leetcode-easy",
        "leetcode-medium",
        "system-design-basics",
        "resume-building",
        "mock-interviews",
    ]
    # weights deliberately favor mock-interviews and leetcode-easy to try to
    # provoke an out-of-order schedule if the tiebreak logic regresses
    role_weights = {
        "mock-interviews": 10.0,
        "leetcode-easy": 9.0,
        "git-github": 1.0,
        "leetcode-medium": 1.0,
        "system-design-basics": 1.0,
        "resume-building": 1.0,
    }

    days = forward_plan(career_gap, role_weights, role="SDE")

    position = {d.topic: i for i, d in enumerate(days)}
    for node in career_gap:
        for prereq in PREREQS[node]:
            if prereq in position:
                assert position[prereq] < position[node], (
                    f"{node} scheduled before its prerequisite {prereq}"
                )


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


def test_generate_roadmap_is_bounded_by_horizon_not_the_entire_gap():
    # item 2c regression: student-1 has 26 total unsatisfied nodes; the old
    # code dumped every one of them instead of stopping at a sensible horizon.
    days = generate_roadmap("student-1")

    assert len(days) < 26
    horizon_end = date.today() + timedelta(days=ROADMAP_HORIZON_DAYS)
    assert all(date.fromisoformat(d.day) < horizon_end for d in days)


def test_generate_roadmap_never_exceeds_three_items_per_day():
    days = generate_roadmap("student-1")
    from collections import Counter

    counts = Counter(d.day for d in days)
    assert all(count <= 3 for count in counts.values())


def test_goal_type_classification_lives_in_dag_not_duplicated_in_roadmap():
    # item 2e regression: roadmap.py used to keep its own hardcoded
    # CAREER_NODES set duplicating dag.py's knowledge.
    import backend.logic.roadmap as roadmap_module

    assert not hasattr(roadmap_module, "CAREER_NODES")

    from backend.logic.dag import NODE_GOAL_TYPE

    academic_gap, career_gap = roadmap_module._split_gap_by_type(list(NODE_GOAL_TYPE.keys()))
    assert set(career_gap) == {n for n, t in NODE_GOAL_TYPE.items() if t == "career"}
    assert set(academic_gap) == {n for n, t in NODE_GOAL_TYPE.items() if t == "academic"}
