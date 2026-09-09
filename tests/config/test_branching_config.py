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


# ---- semantic checks beyond the schema ----

from src.exceptions import InfeasibleConfigError  # noqa: E402


def _branching(**overrides):
    b = {
        "Probability of branching": {"Fixed": 0.3},
        "Maximum nesting depth": {"Fixed": 1},
        "Maximum branches": {"Fixed": 2},
        "Firing": "probabilistic",
        "Probability distribution": "dirichlet",
    }
    b.update(overrides)
    return b


def _multi_rate(periodic_type):
    return {"Periodic type": periodic_type, "Period": {"Fixed": 1000},
            "Total utilization": {"Fixed": 0.5}}


def test_branching_with_all_periodic_type_is_rejected():
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = _branching()
    cfg["Properties"] = {"Multi-rate": _multi_rate("All")}
    with pytest.raises(InfeasibleConfigError, match="'Periodic type' All"):
        ConfigValidator(cfg).validate()


@pytest.mark.parametrize("periodic_type", ["IO", "Entry"])
def test_removed_periodic_types_are_rejected_by_the_schema(periodic_type):
    cfg = _base_chain_config()
    cfg["Properties"] = {"Multi-rate": _multi_rate(periodic_type)}
    with pytest.raises(SchemaError):
        ConfigValidator(cfg).validate()


@pytest.mark.parametrize("periodic_type", ["DAG", "Chain"])
def test_branching_with_dag_or_chain_periodic_type_is_accepted(periodic_type):
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = _branching(Accounting="max-branch")
    cfg["Properties"] = {"Multi-rate": _multi_rate(periodic_type)}
    ConfigValidator(cfg).validate()


def test_periodic_type_chain_requires_chain_based_method():
    cfg = {
        "Seed": 0, "Number of DAGs": 1,
        "Graph structure": {
            "Generation method": "G(n, p)", "Number of nodes": {"Fixed": 5},
            "Number of source nodes": {"Fixed": 1}, "Number of sink nodes": {"Fixed": 1},
            "Probability of edge existence": {"Fixed": 0.3},
        },
        "Properties": {"Multi-rate": _multi_rate("Chain")},
        "Output formats": {"Naming of combination directory": "Abbreviation",
                           "DAG": {"YAML": True}},
    }
    with pytest.raises(InfeasibleConfigError, match="Chain-based"):
        ConfigValidator(cfg).validate()


@pytest.mark.parametrize("option", [{"Fixed": 1}, {"Random": [1, 3]}, {"Combination": "(1, 3, 1)"}])
def test_maximum_branches_below_two_is_rejected(option):
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = _branching(**{"Maximum branches": option})
    with pytest.raises(InfeasibleConfigError, match="Maximum branches"):
        ConfigValidator(cfg).validate()


def test_probability_of_branching_outside_unit_interval_is_rejected():
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = _branching(**{"Probability of branching": {"Fixed": 1.5}})
    with pytest.raises(InfeasibleConfigError, match="Probability of branching"):
        ConfigValidator(cfg).validate()


def test_expected_accounting_requires_probabilistic_firing():
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = _branching(Firing="deterministic", Accounting="expected")
    with pytest.raises(InfeasibleConfigError, match="expected"):
        ConfigValidator(cfg).validate()


def test_invalid_accounting_value_is_rejected_by_schema():
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = _branching(Accounting="worst")
    with pytest.raises(SchemaError):
        ConfigValidator(cfg).validate()


def test_sub_chain_length_option_is_accepted():
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = _branching(**{"Sub-chain length": {"Random": [1, 2, 3]}})
    ConfigValidator(cfg).validate()


def test_ccr_without_base_quantity_is_rejected():
    cfg = _base_chain_config()
    cfg["Properties"] = {"CCR": {"Fixed": 1.0}}
    with pytest.raises(InfeasibleConfigError, match="CCR"):
        ConfigValidator(cfg).validate()


@pytest.mark.parametrize("minimum, message", [({"Fixed": 1}, "Minimum branches"),
                                              ({"Fixed": 4}, "must not exceed")])
def test_minimum_branches_bounds_are_checked(minimum, message):
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = _branching(**{"Maximum branches": {"Fixed": 3},
                                                        "Minimum branches": minimum})
    with pytest.raises(InfeasibleConfigError, match=message):
        ConfigValidator(cfg).validate()


def test_minimum_branches_equal_to_maximum_is_accepted():
    cfg = _base_chain_config()
    cfg["Graph structure"]["Branching"] = _branching(**{"Maximum branches": {"Fixed": 3},
                                                        "Minimum branches": {"Fixed": 3}})
    ConfigValidator(cfg).validate()
