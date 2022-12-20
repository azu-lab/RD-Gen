from src.config import Config


def get_combo_config() -> dict:
    combo_config = {
        "Number of DAGs": 1,
        "Graph structure": {"Generation method": "G(n, p)", "Number of nodes": {"Fixed": 1}},
        "Properties": {
            "End-to-end deadline": {"Ratio of deadline to critical path": {"Random": [1.0, 1.1]}}
        },
        "Output formats": {"DAG": {"YAML": True}},
    }
    return combo_config


class TestConfig:
    def test_remove_random_fixed(self):
        combo_config = get_combo_config()
        combo_config.update({"_": {"_": {"_": {"_": {"_": {"Fixed": 1}}}}}})
        Config._remove_random_fixed(combo_config["Graph structure"])
        assert combo_config["Graph structure"] == {
            "Generation method": "G(n, p)",
            "Number of nodes": 1,
        }

        Config._remove_random_fixed(combo_config["Properties"])
        assert combo_config["Properties"] == {
            "End-to-end deadline": {"Ratio of deadline to critical path": [1.0, 1.1]}
        }
