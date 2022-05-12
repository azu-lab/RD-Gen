
from typing import Dict

from src.config_format.format import Format
from src.input_parameter import InputParameter


class ConfigLoader():
    def __init__(
        self,
        format: Format,
        cfg_raw: Dict
    ) -> None:
        self._format = format
        self._cfg_raw = cfg_raw
        self._validate()

    def load(self) -> Dict:
        self._input_params = {}
        for input_top_param, value in self._cfg_raw.items():
            self._input_params[input_top_param] = InputParameter(
                input_top_param,
                value,
                self._format
            )

        return self._input_params

    def _validate(self) -> None:
        pass  # TODO
