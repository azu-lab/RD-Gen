class Config:
    def __init__(self, combo_config: dict) -> None:
        self._remove_random_fixed(combo_config["Graph structure"])
        self._remove_random_fixed(combo_config["Properties"])
        self._config = combo_config

    @property
    def number_of_dags(self) -> int:
        return self._config["Number of DAGs"]

    @property
    def graph_structure(self) -> dict:
        return self._config["Graph structure"]

    @property
    def properties(self) -> dict:
        return self._config["Properties"]

    @property
    def output_formats(self) -> dict:
        return self._config["Output formats"]

    @staticmethod
    def _remove_random_fixed(param_dict: dict) -> None:
        for k, v in param_dict.items():
            if set(v.keys()) <= {"Random", "Fixed"}:
                # Remove
                value = list(v.values())
                assert len(value) == 1
                param_dict[k] = value[0]
                break
            else:
                Config._remove_random_fixed(v)
