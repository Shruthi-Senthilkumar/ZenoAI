import networkx as nx

from backend.logic.dag import PREREQS, build_dag, first_unsatisfied_node


def test_build_dag_is_a_dag_with_expected_edges():
    g = build_dag()
    assert nx.is_directed_acyclic_graph(g)
    assert g.has_edge("limits", "derivatives")
    assert g.has_edge("derivatives", "integrals")
    assert g.has_edge("arrays", "dsa-graphs")
    assert g.has_edge("hash-tables", "dsa-graphs")
    assert g.has_edge("python-basics", "oop")


def test_dag_has_roughly_thirty_nodes_mixing_academic_and_career():
    g = build_dag()
    assert 25 <= g.number_of_nodes() <= 35
    academic_examples = {"limits", "derivatives", "arrays", "oop"}
    career_examples = {"git-github", "leetcode-easy", "resume-building", "mock-interviews"}
    assert academic_examples.issubset(PREREQS.keys())
    assert career_examples.issubset(PREREQS.keys())


def test_first_unsatisfied_node_respects_topological_order():
    g = build_dag()
    order = first_unsatisfied_node(g, satisfied=set())
    # every node's prerequisites must appear before it
    position = {node: i for i, node in enumerate(order)}
    for node, prereqs in PREREQS.items():
        for p in prereqs:
            assert position[p] < position[node]
    assert set(order) == set(g.nodes)


def test_first_unsatisfied_node_skips_satisfied_topics():
    g = build_dag()
    satisfied = {"python-basics", "arrays", "hash-tables"}
    order = first_unsatisfied_node(g, satisfied)
    assert not satisfied & set(order)
    # first remaining node should not be one already known
    assert order[0] not in satisfied


def test_a_student_who_knows_everything_gets_an_empty_gap_list():
    g = build_dag()
    order = first_unsatisfied_node(g, satisfied=set(PREREQS.keys()))
    assert order == []
