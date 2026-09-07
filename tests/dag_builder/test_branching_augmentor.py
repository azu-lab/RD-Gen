import random

import networkx as nx
import pytest

from src.branching_validator import BranchingValidator
from src.config import Config
from src.dag_builder.branching_augmentor import BranchingAugmentor


def _chain_config(prob_b=1.0, max_depth=1, max_branches=2, firing="probabilistic",
                  dist="uniform-normalize"):
    """Build a Config object directly (bypass YAML loading)."""
    raw = {
        "Seed": 0,
        "Number of DAGs": 1,
        "Graph structure": {
            "Generation method": "Chain-based",
            "Number of chains": {"Fixed": 1},
            "Main sequence length": {"Fixed": 5},
            "Number of sub sequences": {"Fixed": 0},
            "Branching": {
                "Probability of branching": {"Fixed": prob_b},
                "Maximum nesting depth": {"Fixed": max_depth},
                "Maximum branches": {"Fixed": max_branches},
                "Firing": firing,
                "Probability distribution": dist,
            },
        },
        "Properties": {"Execution time": {"Fixed": 1}},
        "Output formats": {
            "Naming of combination directory": "Abbreviation",
            "DAG": {"YAML": True},
        },
    }
    cfg = Config(raw)
    cfg.optimize()
    return cfg


def _chain_dag(n=5):
    g = nx.DiGraph()
    for i in range(n):
        g.add_node(i, node_type="regular", execution_time=1)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    return g


def test_chain_augment_creates_v_ent_v_ext_pairs():
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=1, max_branches=2)
    aug = BranchingAugmentor(cfg)
    g = aug.augment(_chain_dag(5), layout_hint="chain")
    vents = [n for n, a in g.nodes(data=True) if a.get("node_type") == "v_ent"]
    vexts = [n for n, a in g.nodes(data=True) if a.get("node_type") == "v_ext"]
    assert len(vents) >= 1
    assert len(vents) == len(vexts)
    BranchingValidator.assert_valid(g, "probabilistic")


def test_chain_augment_no_branching_when_max_depth_zero():
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=0, max_branches=2)
    aug = BranchingAugmentor(cfg)
    g_in = _chain_dag(5)
    g_out = aug.augment(g_in, layout_hint="chain")
    assert all(a.get("node_type", "regular") == "regular" for _, a in g_out.nodes(data=True))


def test_chain_augment_firing_prob_sums_to_one():
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=4, firing="probabilistic")
    aug = BranchingAugmentor(cfg)
    g = aug.augment(_chain_dag(6), layout_hint="chain")
    for n, a in g.nodes(data=True):
        if a.get("node_type") != "v_ent":
            continue
        out_probs = [d["firing_prob"] for _, _, d in g.out_edges(n, data=True)]
        assert abs(sum(out_probs) - 1.0) < 1e-9


def test_chain_augment_deterministic_omits_firing_prob():
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=1, max_branches=2, firing="deterministic")
    aug = BranchingAugmentor(cfg)
    g = aug.augment(_chain_dag(5), layout_hint="chain")
    for n, a in g.nodes(data=True):
        if a.get("node_type") != "v_ent":
            continue
        for _, _, d in g.out_edges(n, data=True):
            assert "firing_prob" not in d
            assert "branch_id" in d


def test_chain_augment_v_ent_v_ext_have_zero_exec_time():
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=1, max_branches=2)
    aug = BranchingAugmentor(cfg)
    g = aug.augment(_chain_dag(5), layout_hint="chain")
    for n, a in g.nodes(data=True):
        if a.get("node_type") in ("v_ent", "v_ext"):
            assert a.get("execution_time") == 0


def test_chain_augment_no_orphan_sources_at_depth_two():
    """Regression: max_depth>=2 must not leave orphan inner v_ent nodes
    (the original merge-back bug created 18 sources where 1 was expected)."""
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=3)
    aug = BranchingAugmentor(cfg)
    g = aug.augment(_chain_dag(5), layout_hint="chain")
    sources = [n for n in g.nodes() if g.in_degree(n) == 0]
    assert len(sources) == 1, f"expected 1 source node, got {len(sources)}: {sources}"
    # Inner v_ent nodes (those that are not the unique DAG source) must have a predecessor.
    # The single DAG source may legitimately be a v_ent when it replaces the chain root.
    dag_source = sources[0]
    for n in g.nodes():
        if n == dag_source:
            continue
        if g.nodes[n].get("node_type") == "v_ent" and g.in_degree(n) == 0:
            raise AssertionError(f"orphan inner v_ent found: {n}")


def _gnp_dag(n=8, p=0.3, seed=0):
    random.seed(seed)
    g = nx.DiGraph()
    for i in range(n):
        g.add_node(i, node_type="regular", execution_time=1)
    for i in range(n):
        for j in range(n):
            if i < j and random.random() < p:
                g.add_edge(i, j)
    return g


def test_gnp_augment_creates_v_ent_v_ext_pairs():
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=1, max_branches=2)
    # NOTE: Branching subsection is layout-agnostic; reusing _chain_config
    cfg.graph_structure["Probability of edge existence"] = 0.3
    aug = BranchingAugmentor(cfg)
    g = aug.augment(_gnp_dag(n=6, p=0.5, seed=1), layout_hint="gnp")
    vents = [n for n, a in g.nodes(data=True) if a.get("node_type") == "v_ent"]
    vexts = [n for n, a in g.nodes(data=True) if a.get("node_type") == "v_ext"]
    assert len(vents) >= 1
    assert len(vents) == len(vexts)
    BranchingValidator.assert_valid(g, "probabilistic")


def test_gnp_augment_firing_prob_sums_to_one():
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=3)
    cfg.graph_structure["Probability of edge existence"] = 0.3
    aug = BranchingAugmentor(cfg)
    g = aug.augment(_gnp_dag(n=8, p=0.4, seed=2), layout_hint="gnp")
    for n, a in g.nodes(data=True):
        if a.get("node_type") != "v_ent":
            continue
        out_probs = [d["firing_prob"] for _, _, d in g.out_edges(n, data=True)]
        assert abs(sum(out_probs) - 1.0) < 1e-9


def test_gnp_augment_dirichlet_distribution():
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=1, max_branches=3, dist="dirichlet")
    cfg.graph_structure["Probability of edge existence"] = 0.3
    aug = BranchingAugmentor(cfg)
    g = aug.augment(_gnp_dag(n=6, p=0.4, seed=3), layout_hint="gnp")
    BranchingValidator.assert_valid(g, "probabilistic")


def test_gnp_augment_no_orphan_sources_at_depth_two():
    """Regression: gnp mode at depth>=2 must not produce orphan v_ent nodes."""
    random.seed(42)
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=3)
    cfg.graph_structure["Probability of edge existence"] = 0.3
    aug = BranchingAugmentor(cfg)
    g = aug.augment(_gnp_dag(n=6, p=0.3, seed=4), layout_hint="gnp")
    for n in g.nodes():
        if g.nodes[n].get("node_type") == "v_ent":
            assert g.in_degree(n) >= 1 or n == min(g.nodes()), \
                f"orphan v_ent found: {n}"
    BranchingValidator.assert_valid(g, "probabilistic")


# ---- reproducibility, protected nodes, per-DAG parameters ----

from src.common import Util  # noqa: E402


def _augment_twice(cfg, host_factory, hint):
    outs = []
    for _ in range(2):
        random.seed(7)
        outs.append(BranchingAugmentor(cfg).augment(host_factory(), hint))
    return outs


@pytest.mark.parametrize("dist", ["dirichlet", "uniform-normalize"])
def test_same_seed_gives_identical_output_without_numpy(dist):
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=3, dist=dist)
    cfg.graph_structure["Probability of edge existence"] = 0.3
    a, b = _augment_twice(cfg, lambda: _gnp_dag(n=8, p=0.4, seed=2), "gnp")
    assert nx.utils.graphs_equal(a, b)
    probs = [d["firing_prob"] for _, _, d in a.edges(data=True) if "firing_prob" in d]
    assert probs and all(0.0 < p < 1.0 for p in probs)


def test_source_and_sink_nodes_are_never_replaced():
    random.seed(1)
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=2)
    g = BranchingAugmentor(cfg).augment(_chain_dag(6), layout_hint="chain")
    assert g.nodes[0]["node_type"] == "regular" and g.nodes[5]["node_type"] == "regular"
    for n in Util.get_source_nodes(g) + Util.get_sink_nodes(g):
        assert g.nodes[n]["node_type"] == "regular"
    assert sum(1 for _, a in g.nodes(data=True) if a["node_type"] == "v_ent") >= 4


def test_single_node_dag_is_left_untouched():
    random.seed(1)
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=2)
    g = BranchingAugmentor(cfg).augment(_chain_dag(1), layout_hint="chain")
    assert list(g.nodes()) == [0] and g.nodes[0]["node_type"] == "regular"


def _two_chain_host():
    g = nx.DiGraph()
    for n in (0, 1, 2):
        g.add_node(n, node_type="regular", execution_time=1, chain_id=0)
    for n in (3, 4, 5):
        g.add_node(n, node_type="regular", execution_time=1, chain_id=1)
    g.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])  # 2 -> 3 vertical link
    return g


def test_chain_heads_are_protected_and_chain_id_is_inherited():
    random.seed(3)
    cfg = _chain_config(prob_b=1.0, max_depth=1, max_branches=2)
    g = BranchingAugmentor(cfg).augment(_two_chain_host(), layout_hint="chain")
    # Heads 0 and 3 (3 is not a source) and sink 5 survive; 1, 2, 4 are replaced.
    for n in (0, 3, 5):
        assert n in g and g.nodes[n]["node_type"] == "regular"
    for n in (1, 2, 4):
        assert n not in g
    assert all("chain_id" in a for _, a in g.nodes(data=True))
    chains = Util.chains(g)
    assert Util.chain_head(g, chains[0]) == 0 and Util.chain_head(g, chains[1]) == 3
    assert sum(1 for _, a in g.nodes(data=True) if a["node_type"] == "v_ent") == 3
    # New nodes inherit the chain of the node they replaced: the unit built from
    # node 4 (chain 1) lies between 3 and 5.
    for n in nx.descendants(g, 3) - {5}:
        assert g.nodes[n]["chain_id"] == 1


def test_branching_parameters_are_drawn_once_per_dag(mocker):
    random.seed(5)
    cfg = _chain_config(prob_b=1.0, max_depth=3, max_branches=2)
    cfg.graph_structure["Branching"]["Probability of branching"] = [1.0, 1.0]
    cfg.graph_structure["Branching"]["Maximum nesting depth"] = [3, 3]
    cfg.graph_structure["Branching"]["Maximum branches"] = [2, 2]
    spy = mocker.spy(Util, "random_choice")
    BranchingAugmentor(cfg).augment(_chain_dag(6), layout_hint="chain")
    for option in (cfg.probability_of_branching, cfg.maximum_nesting_depth, cfg.maximum_branches):
        assert sum(1 for c in spy.call_args_list if c.args[0] is option) == 1


def test_sub_chain_length_option_controls_branch_body_length():
    random.seed(2)
    cfg = _chain_config(prob_b=1.0, max_depth=1, max_branches=2)
    cfg.graph_structure["Branching"]["Sub-chain length"] = 1
    g = BranchingAugmentor(cfg).augment(_chain_dag(5), layout_hint="chain")
    # 3 replaced nodes (1, 2, 3), each -> v_ent + 2 * 1 sub-node + v_ext = 4 nodes.
    assert g.number_of_nodes() == 2 + 3 * 4


def test_marginal_prob_and_retry_count_are_recorded():
    random.seed(4)
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=2)
    g = BranchingAugmentor(cfg).augment(_chain_dag(5), layout_hint="chain")
    assert g.graph["augmentation_retries"] == 0
    for n, a in g.nodes(data=True):
        assert 0.0 < a["marginal_prob"] <= 1.0
    for n in Util.get_source_nodes(g):
        assert g.nodes[n]["marginal_prob"] == 1.0
    det = _chain_config(prob_b=1.0, max_depth=1, max_branches=2, firing="deterministic")
    g = BranchingAugmentor(det).augment(_chain_dag(5), layout_hint="chain")
    assert not any("marginal_prob" in a for _, a in g.nodes(data=True))


# ---- edge cases of the branching parameters ----

def _count_units(g):
    return sum(1 for _, a in g.nodes(data=True) if a["node_type"] == "v_ent")


def test_zero_branching_probability_inserts_nothing():
    random.seed(0)
    cfg = _chain_config(prob_b=0.0, max_depth=3, max_branches=3)
    g = BranchingAugmentor(cfg).augment(_chain_dag(8), layout_hint="chain")
    assert _count_units(g) == 0 and g.number_of_nodes() == 8


def test_unit_branching_probability_replaces_every_candidate():
    random.seed(0)
    cfg = _chain_config(prob_b=1.0, max_depth=1, max_branches=2)
    g = BranchingAugmentor(cfg).augment(_chain_dag(8), layout_hint="chain")
    assert _count_units(g) == 6  # all nodes except the source and the sink


def test_maximum_branches_two_gives_exactly_two_branches():
    random.seed(0)
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=2)
    g = BranchingAugmentor(cfg).augment(_chain_dag(6), layout_hint="chain")
    for n, a in g.nodes(data=True):
        if a["node_type"] == "v_ent":
            assert g.out_degree(n) == 2


def test_small_branching_probability_is_resolved():
    """p_b = 0.01 must be honoured (no 1% discretisation floor)."""
    random.seed(0)
    cfg = _chain_config(prob_b=0.01, max_depth=1, max_branches=2)
    units = sum(_count_units(BranchingAugmentor(cfg).augment(_chain_dag(102), layout_hint="chain"))
                for _ in range(50))
    assert 20 <= units <= 90  # 5000 candidates * 0.01 = 50 expected


def test_minimum_branches_fixes_the_branch_count():
    random.seed(0)
    cfg = _chain_config(prob_b=1.0, max_depth=2, max_branches=3)
    cfg.graph_structure["Branching"]["Minimum branches"] = 3
    g = BranchingAugmentor(cfg).augment(_chain_dag(6), layout_hint="chain")
    assert all(g.out_degree(n) == 3 for n, a in g.nodes(data=True) if a["node_type"] == "v_ent")
