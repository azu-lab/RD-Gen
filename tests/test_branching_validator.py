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
