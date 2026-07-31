import networkx as nx
import pytest

from src.config import Config, ConfigValidator
from src.dag_builder import DAGBuilderFactory
from src.branching_validator import BranchingValidator


def _chain_branching_config():
    return {
        "Seed": 0,
        "Number of DAGs": 2,
        "Graph structure": {
            "Generation method": "Chain-based",
            "Number of chains": {"Fixed": 2},
            "Main sequence length": {"Fixed": 4},
            "Number of sub sequences": {"Fixed": 0},
            "Branching": {
                "Probability of branching": {"Fixed": 0.5},
                "Maximum nesting depth": {"Fixed": 2},
                "Maximum branches": {"Fixed": 3},
                "Firing": "probabilistic",
                "Probability distribution": "uniform-normalize",
            },
        },
        "Properties": {"Execution time": {"Fixed": 5}},
        "Output formats": {
            "Naming of combination directory": "Abbreviation",
            "DAG": {"YAML": True},
        },
    }


def test_factory_returns_augmented_builder_when_branching_set():
    raw = _chain_branching_config()
    ConfigValidator(raw).validate()
    cfg = Config(raw)
    cfg.optimize()
    cfg.set_random_seed()
    builder = DAGBuilderFactory.create_instance(cfg)
    dags = list(builder.build())
    assert len(dags) == cfg.number_of_dags
    for g in dags:
        BranchingValidator.assert_valid(g, "probabilistic")
        assert any(a.get("node_type") == "v_ent" for _, a in g.nodes(data=True))


def test_factory_returns_plain_builder_when_branching_absent():
    raw = _chain_branching_config()
    del raw["Graph structure"]["Branching"]
    ConfigValidator(raw).validate()
    cfg = Config(raw)
    cfg.optimize()
    cfg.set_random_seed()
    builder = DAGBuilderFactory.create_instance(cfg)
    dags = list(builder.build())
    assert len(dags) == cfg.number_of_dags
    for g in dags:
        assert all(a.get("node_type", "regular") == "regular"
                   for _, a in g.nodes(data=True))


def _fanin_branching_config():
    return {
        "Seed": 0,
        "Number of DAGs": 2,
        "Graph structure": {
            "Generation method": "Fan-in/Fan-out",
            "Number of nodes": {"Fixed": 10},
            "Number of source nodes": {"Fixed": 2},
            "Number of sink nodes": {"Fixed": 1},
            "In-degree": {"Fixed": 3},
            "Out-degree": {"Fixed": 3},
            "Ensure weakly connected": True,
            "Branching": {
                "Probability of branching": {"Fixed": 0.5},
                "Maximum nesting depth": {"Fixed": 2},
                "Maximum branches": {"Fixed": 3},
                "Firing": "probabilistic",
                "Probability distribution": "uniform-normalize",
            },
        },
        "Properties": {"Execution time": {"Fixed": 5}},
        "Output formats": {
            "Naming of combination directory": "Abbreviation",
            "DAG": {"YAML": True},
        },
    }


def test_factory_returns_augmented_builder_for_fanin_branching():
    raw = _fanin_branching_config()
    ConfigValidator(raw).validate()
    cfg = Config(raw)
    cfg.optimize()
    cfg.set_random_seed()
    builder = DAGBuilderFactory.create_instance(cfg)
    dags = list(builder.build())
    assert len(dags) == cfg.number_of_dags
    for g in dags:
        BranchingValidator.assert_valid(g, "probabilistic")
        assert any(a.get("node_type") == "v_ent" for _, a in g.nodes(data=True))
