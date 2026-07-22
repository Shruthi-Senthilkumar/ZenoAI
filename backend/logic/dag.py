"""Skill/subject prerequisite DAG (PRD §4, Backend Spec §5).

Hand-authored adjacency list — NOT LLM-generated — so prerequisite
accuracy is guaranteed rather than model-dependent. ~30 nodes for
hackathon scope, mixing academic topics (math, CS fundamentals) and
career skills (DSA practice, git/GitHub workflow, resume prep).

`satisfied` (passed to `first_unsatisfied_node`) is built from the
student's evidence — LMS scores, GitHub/LeetCode history, and intake
answers (Backend Spec §11, PRD §7) — so a student who already knows a
topic never gets it scheduled into their roadmap.

`NODE_GOAL_TYPE` is the single source of truth for whether a node is
an academic topic or a career skill. roadmap.py used to keep its own
duplicate `CAREER_NODES` set for this — that let the two definitions
drift silently. Classification lives here, next to the nodes it
classifies, so a new PREREQS entry without a matching NODE_GOAL_TYPE
entry fails fast at import time instead of drifting unnoticed.
"""

from typing import Literal

import networkx as nx

PREREQS: dict[str, list[str]] = {
    # --- Academic: math track ---
    "limits": [],
    "derivatives": ["limits"],
    "integrals": ["derivatives"],
    "differential-equations": ["integrals"],
    "linear-algebra": ["python-basics"],
    "probability": ["linear-algebra"],
    "statistics": ["probability"],

    # --- Academic: CS fundamentals ---
    "python-basics": [],
    "oop": ["python-basics"],
    "arrays": ["python-basics"],
    "hash-tables": ["arrays"],
    "linked-lists": ["arrays"],
    "stacks-queues": ["linked-lists"],
    "recursion": ["arrays"],
    "sorting": ["arrays", "recursion"],
    "trees": ["recursion"],
    "binary-search-trees": ["trees"],
    "heaps": ["trees"],
    "dsa-graphs": ["arrays", "hash-tables"],
    "graph-traversal": ["dsa-graphs"],
    "dynamic-programming": ["recursion", "sorting"],
    "dbms": ["oop"],
    "sql": ["dbms"],
    "operating-systems": ["oop"],
    "computer-networks": ["operating-systems"],

    # --- Career skills ---
    "git-github": ["python-basics"],
    "leetcode-easy": ["arrays", "hash-tables"],
    "leetcode-medium": ["leetcode-easy", "dynamic-programming"],
    "system-design-basics": ["computer-networks", "dbms"],
    "resume-building": ["git-github"],
    "mock-interviews": ["leetcode-medium", "system-design-basics", "resume-building"],
}

GoalType = Literal["academic", "career"]

_CAREER_NODE_NAMES = {
    "git-github",
    "leetcode-easy",
    "leetcode-medium",
    "system-design-basics",
    "resume-building",
    "mock-interviews",
}

NODE_GOAL_TYPE: dict[str, GoalType] = {
    node: ("career" if node in _CAREER_NODE_NAMES else "academic") for node in PREREQS
}

assert set(NODE_GOAL_TYPE) == set(PREREQS), "NODE_GOAL_TYPE and PREREQS have drifted apart"


def goal_type_of(node: str) -> GoalType:
    return NODE_GOAL_TYPE.get(node, "academic")


def build_dag() -> nx.DiGraph:
    """Build a directed graph from PREREQS: edges point prereq -> node."""
    g = nx.DiGraph()
    g.add_nodes_from(PREREQS)
    for node, prereqs in PREREQS.items():
        for p in prereqs:
            g.add_edge(p, node)
    return g


def first_unsatisfied_node(g: nx.DiGraph, satisfied: set[str]) -> list[str]:
    """Return nodes in topological order, skipping anything already satisfied.

    `satisfied` is built from the student's evidence (LMS scores,
    GitHub/LeetCode history, intake answers) — a student who already
    knows a topic never gets it scheduled.
    """
    return [n for n in nx.topological_sort(g) if n not in satisfied]
