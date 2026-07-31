import pytest
from schema import SchemaError

from src.config.config_validator import ConfigValidator


def _base_chain_config():
    return {
        "Seed": 0,
        "Number of DAGs": 1,
        "Graph structure": {
            "Generation method": "Chain-based",
            "Number of chains": {"Fixed": 2},
            "Main sequence length": {"Fixed": 3},
            "Number of sub sequences": {"Fixed": 0},
        },
        "Properties": {"Execution time": {"Fixed": 5}},
        "Output formats": {
            "Naming of combination directory": "Abbreviation",
            "DAG": {"YAML": True},
        },
    }


def test_branching_valid_chain_probabilistic():
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = {
        "Probability of branching": {"Fixed": 0.3},
        "Maximum nesting depth": {"Fixed": 2},
        "Maximum branches": {"Fixed": 3},
        "Firing": "probabilistic",
        "Probability distribution": "dirichlet",
        "Dirichlet alpha": 1.0,
    }
    ConfigValidator(cfg).validate()  # must not raise


def test_branching_valid_chain_deterministic_no_alpha():
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = {
        "Probability of branching": {"Combination": [0.1, 0.3, 0.5]},
        "Maximum nesting depth": {"Combination": [1, 2, 3]},
        "Maximum branches": {"Fixed": 2},
        "Firing": "deterministic",
        "Probability distribution": "uniform-normalize",
    }
    ConfigValidator(cfg).validate()


def test_branching_invalid_firing_value():
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = {
        "Probability of branching": {"Fixed": 0.3},
        "Maximum nesting depth": {"Fixed": 1},
        "Maximum branches": {"Fixed": 2},
        "Firing": "bogus",
        "Probability distribution": "dirichlet",
    }
    with pytest.raises(SchemaError):
        ConfigValidator(cfg).validate()


def test_branching_absent_is_backward_compat():
    cfg = _base_chain_config()
    ConfigValidator(cfg).validate()  # no Branching key, must pass
