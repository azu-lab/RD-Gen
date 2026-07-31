import copy

import pytest
from schema import SchemaError

from src.config.config_validator import ConfigValidator


def get_valid_config() -> dict:
    return {
        "Seed": 0,
        "Number of DAGs": 1,
        "Graph structure": {
            "Generation method": "G(n, p)",
            "Number of nodes": {"Fixed": 5},
            "Number of source nodes": {"Fixed": 1},
            "Number of sink nodes": {"Fixed": 1},
            "Probability of edge existence": {"Fixed": 0.5},
        },
        "Properties": {
            "Execution time": {"Fixed": 1},
        },
        "Output formats": {
            "Naming of combination directory": "Abbreviation",
            "DAG": {"YAML": True},
        },
    }


class TestConfigValidatorDeadlineMode:
    def test_no_end_to_end_deadline_is_valid(self):
        config_raw = get_valid_config()
        ConfigValidator(config_raw).validate()  # Should not raise.

    def test_arbitrary_mode_requires_ratio(self):
        config_raw = get_valid_config()
        config_raw["Properties"]["End-to-end deadline"] = {"Deadline mode": "Arbitrary"}
        with pytest.raises(SchemaError):
            ConfigValidator(config_raw).validate()

    def test_arbitrary_mode_default_with_ratio_is_valid(self):
        config_raw = get_valid_config()
        config_raw["Properties"]["End-to-end deadline"] = {
            "Ratio of deadline to critical path": {"Fixed": 1.1}
        }
        ConfigValidator(config_raw).validate()  # Should not raise (default mode).

    def test_implicit_mode_requires_multi_rate(self):
        config_raw = get_valid_config()
        config_raw["Properties"]["End-to-end deadline"] = {"Deadline mode": "Implicit"}
        with pytest.raises(SchemaError):
            ConfigValidator(config_raw).validate()

    def test_implicit_mode_requires_periodic_type_entry(self):
        config_raw = get_valid_config()
        config_raw["Properties"]["End-to-end deadline"] = {"Deadline mode": "Implicit"}
        config_raw["Properties"]["Multi-rate"] = {
            "Periodic type": "All",
            "Period": {"Fixed": 100},
        }
        with pytest.raises(SchemaError):
            ConfigValidator(config_raw).validate()

    def test_implicit_mode_with_periodic_type_entry_is_valid(self):
        config_raw = get_valid_config()
        config_raw["Properties"]["End-to-end deadline"] = {"Deadline mode": "Implicit"}
        config_raw["Properties"]["Multi-rate"] = {
            "Periodic type": "Entry",
            "Period": {"Fixed": 100},
        }
        ConfigValidator(config_raw).validate()  # Should not raise.

    def test_constrained_mode_with_periodic_type_entry_is_valid(self):
        config_raw = get_valid_config()
        config_raw["Properties"]["End-to-end deadline"] = {"Deadline mode": "Constrained"}
        config_raw["Properties"]["Multi-rate"] = {
            "Periodic type": "Entry",
            "Period": {"Fixed": 100},
        }
        ConfigValidator(config_raw).validate()  # Should not raise.

    def test_original_config_not_mutated(self):
        config_raw = get_valid_config()
        config_raw["Properties"]["End-to-end deadline"] = {"Deadline mode": "Implicit"}
        config_raw["Properties"]["Multi-rate"] = {
            "Periodic type": "Entry",
            "Period": {"Fixed": 100},
        }
        before = copy.deepcopy(config_raw)
        ConfigValidator(config_raw).validate()
        assert config_raw == before
