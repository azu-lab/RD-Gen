import networkx as nx
import pytest

from src.branching_structure import BranchingConstraintError, BranchingStructure


def nested_pdag():
    """0 -> u0[ b0: 2 | b1: 3 -> u1[ b0: 7 | b1: 8 ] -> 4 ] -> 10 with weights below."""
    g = nx.DiGraph()
    weights = {0: 10, 2: 5, 3: 1, 4: 2, 7: 3, 8: 8, 10: 4}
    for n in (0, 2, 3, 4, 7, 8, 10):
        g.add_node(n, node_type="regular", execution_time=weights[n])
    g.add_node(1, node_type="v_ent", branch_unit_id=0, execution_time=0)
    g.add_node(5, node_type="v_ext", branch_unit_id=0, execution_time=0)
    g.add_node(6, node_type="v_ent", branch_unit_id=1, execution_time=0)
    g.add_node(9, node_type="v_ext", branch_unit_id=1, execution_time=0)
    g.add_edge(0, 1)
    g.add_edge(1, 2, branch_id=0, firing_prob=0.6)
    g.add_edge(1, 3, branch_id=1, firing_prob=0.4)
    g.add_edge(2, 5)
    g.add_edge(3, 6)
    g.add_edge(6, 7, branch_id=0, firing_prob=0.5)
    g.add_edge(6, 8, branch_id=1, firing_prob=0.5)
    g.add_edge(7, 9)
    g.add_edge(8, 9)
    g.add_edge(9, 4)
    g.add_edge(4, 5)
    g.add_edge(5, 10)
    return g, weights


def test_nesting_tree():
    g, _ = nested_pdag()
    s = BranchingStructure(g)
    assert s.units == [0, 1]
    assert s.parent == {0: None, 1: (0, 1)}
    assert s.unit_depth == {0: 1, 1: 2}
    assert s.nesting_depth == 2
    assert s.children[None] == [0] and s.children[(0, 1)] == [1]
    assert s.region[2] == (0, 0) and s.region[4] == (0, 1) and s.region[7] == (1, 0)
    assert s.region[6] == (0, 1) and s.region[9] == (0, 1) and s.region[10] is None


def test_marginal_probabilities_multiply_along_nesting():
    g, _ = nested_pdag()
    s = BranchingStructure(g)
    expected = {0: 1, 1: 1, 5: 1, 10: 1, 2: 0.6, 3: 0.4, 6: 0.4, 9: 0.4, 4: 0.4, 7: 0.2, 8: 0.2}
    for n, p in expected.items():
        assert s.marginal_prob(n) == pytest.approx(p)


def test_node_aggregates():
    g, weights = nested_pdag()
    s = BranchingStructure(g)
    assert s.aggregate(weights, "all") == pytest.approx(33)
    assert s.aggregate(weights, "expected") == pytest.approx(20.4)
    assert s.aggregate(weights, "max-branch") == pytest.approx(25)


def test_edge_aggregates_use_deeper_endpoint():
    g, _ = nested_pdag()
    s = BranchingStructure(g)
    edges = {(0, 1): 1, (1, 2): 1, (2, 5): 1, (3, 6): 1, (7, 9): 1, (9, 4): 1}
    assert s.aggregate(edges, "all") == pytest.approx(6)
    assert s.aggregate(edges, "expected") == pytest.approx(3.2)
    assert s.aggregate(edges, "max-branch") == pytest.approx(4)


def test_aggregate_ignores_absent_elements():
    """Weights restricted to one chain must not pick up other units' nodes."""
    g, weights = nested_pdag()
    s = BranchingStructure(g)
    subset = {n: w for n, w in weights.items() if n in (7, 8, 4)}
    assert s.aggregate(subset, "max-branch") == pytest.approx(10)


def test_expected_requires_firing_prob():
    g, weights = nested_pdag()
    for u, v in g.edges():
        g.edges[u, v].pop("firing_prob", None)
    s = BranchingStructure(g)
    with pytest.raises(ValueError):
        s.aggregate(weights, "expected")
    assert s.aggregate(weights, "max-branch") == pytest.approx(25)


def test_v_ext_outside_enclosing_branch_is_rejected():
    g, _ = nested_pdag()
    # Move u1's exit after u0's exit: 7,8 -> 4 -> 5 -> 9 -> 10.
    g.remove_edges_from([(7, 9), (8, 9), (9, 4), (5, 10)])
    g.add_edges_from([(7, 4), (8, 4), (5, 9), (9, 10)])
    with pytest.raises(BranchingConstraintError):
        BranchingStructure(g)


def test_plain_dag_has_no_units():
    g = nx.path_graph(4, create_using=nx.DiGraph)
    s = BranchingStructure(g)
    assert s.units == [] and s.nesting_depth == 0
    assert s.aggregate({n: 1 for n in g.nodes()}, "max-branch") == 4
