import pytest
import networkx as nx

from src.branching_validator import BranchingValidator, BranchingConstraintError


def _make_valid_pdag():
    """A minimal valid pDAG with one branching unit (k=2)."""
    g = nx.DiGraph()
    g.add_node(0, node_type="regular", execution_time=10)
    g.add_node(1, node_type="v_ent", branch_unit_id=0, execution_time=0)
    g.add_node(2, node_type="regular", execution_time=5)
    g.add_node(3, node_type="regular", execution_time=7)
    g.add_node(4, node_type="v_ext", branch_unit_id=0, execution_time=0)
    g.add_edge(0, 1)
    g.add_edge(1, 2, branch_id=0, firing_prob=0.6)
    g.add_edge(1, 3, branch_id=1, firing_prob=0.4)
    g.add_edge(2, 4)
    g.add_edge(3, 4)
    return g


def test_valid_pdag_passes():
    BranchingValidator.assert_valid(_make_valid_pdag(), "probabilistic")


def test_valid_cdag_passes_without_firing_prob():
    """deterministic firing: firing_prob is absent, but branch_id is present."""
    g = _make_valid_pdag()
    for u, v in list(g.edges()):
        if "firing_prob" in g.edges[u, v]:
            del g.edges[u, v]["firing_prob"]
    BranchingValidator.assert_valid(g, "deterministic")


def test_firing_prob_sum_not_one_is_rejected():
    g = _make_valid_pdag()
    g.edges[1, 2]["firing_prob"] = 0.5
    g.edges[1, 3]["firing_prob"] = 0.4  # sum 0.9
    with pytest.raises(BranchingConstraintError):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_branch_vertex_overlap_is_rejected():
    """Branch 0 and branch 1 share a vertex — violates Melani Def III.1."""
    g = _make_valid_pdag()
    g.add_edge(2, 3)  # vertex 3 now reachable from branch 0 too
    with pytest.raises(BranchingConstraintError):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_missing_v_ext_pair_is_rejected():
    g = _make_valid_pdag()
    # delete v_ext to break the pair
    g.remove_node(4)
    with pytest.raises(BranchingConstraintError):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_branch_id_not_contiguous_is_rejected():
    g = _make_valid_pdag()
    # change branch_id 0 -> 2, leaving {1, 2} instead of {0, 1}
    g.edges[1, 2]["branch_id"] = 2
    with pytest.raises(BranchingConstraintError):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_missing_branch_id_is_rejected():
    g = _make_valid_pdag()
    del g.edges[1, 2]["branch_id"]
    with pytest.raises(BranchingConstraintError):
        BranchingValidator.assert_valid(g, "deterministic")


def test_no_branching_dag_passes_trivially():
    """DAG with no v_ent/v_ext should be valid in both firing modes."""
    g = nx.DiGraph()
    g.add_node(0, node_type="regular", execution_time=10)
    g.add_node(1, node_type="regular", execution_time=10)
    g.add_edge(0, 1)
    BranchingValidator.assert_valid(g, "deterministic")
    BranchingValidator.assert_valid(g, "probabilistic")


# ---- extended checks (acyclicity, entry edges, dominance, nesting) ----

from tests.test_branching_structure import nested_pdag  # noqa: E402


def test_nested_pdag_passes_and_returns_structure():
    g, _ = nested_pdag()
    s = BranchingValidator.assert_valid(g, "probabilistic")
    assert s.nesting_depth == 2


def test_cycle_is_rejected():
    g, _ = nested_pdag()
    g.add_edge(10, 0)
    with pytest.raises(BranchingConstraintError, match="cycle"):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_edge_entering_branch_body_is_rejected():
    g, _ = nested_pdag()
    g.add_edge(0, 2)
    with pytest.raises(BranchingConstraintError, match="enters branch"):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_edge_bypassing_body_into_v_ext_is_rejected():
    g, _ = nested_pdag()
    g.add_edge(0, 5)
    with pytest.raises(BranchingConstraintError, match="from outside the branches"):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_branch_not_reaching_v_ext_is_rejected():
    g, _ = nested_pdag()
    g.remove_edge(2, 5)
    with pytest.raises(BranchingConstraintError, match="never reaches v_ext"):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_unit_with_single_branch_is_rejected():
    g, _ = nested_pdag()
    g.remove_edge(6, 8)
    g.remove_node(8)
    with pytest.raises(BranchingConstraintError, match="fewer than two branches"):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_duplicate_v_ent_for_unit_is_rejected():
    g, _ = nested_pdag()
    g.nodes[6]["branch_unit_id"] = 0
    with pytest.raises(BranchingConstraintError):
        BranchingValidator.assert_valid(g, "probabilistic")


def test_dominance_test_independent_of_structure():
    """v_ent must dominate and v_ext post-dominate: checked on a plain diamond."""
    g = nx.DiGraph([(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)])
    dominates = BranchingValidator._dominance_test(g, reverse=False)
    post_dominates = BranchingValidator._dominance_test(g, reverse=True)
    assert dominates(0, 3) and dominates(0, 4) and not dominates(1, 3)
    assert post_dominates(3, 1) and post_dominates(4, 0) and not post_dominates(1, 0)
