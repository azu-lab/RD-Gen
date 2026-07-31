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
    import numpy as np
    random.seed(42)
    np.random.seed(42)  # required because np.random has separate state
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
