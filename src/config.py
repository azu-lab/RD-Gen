from typing import Dict, List, Optional, Union

from src.abbreviation import TO_ORI
from src.input_parameter import InputParameter


class Config():
    def __init__(
        self,
        cfg_raw: Dict
    ) -> None:
        self._cfg = {}
        for input_top_param, value in cfg_raw.items():
            self._cfg[input_top_param.lower()] = InputParameter(
                input_top_param.lower(),
                value
            )

    def get_value(
        self,
        param_name_abb: List[str]
    ) -> Optional[Union[str, int, float, List]]:
        # to original parameter name
        param_names = [TO_ORI[n] for n in param_name_abb]

        try:
            param = self._cfg[param_names[0]]
            if len(param_names) > 1:
                for param_name in param_names[1:]:
                    param = param.children[param_name]

            return param.value

        except KeyError:
            return None

    def get_param(
        self,
        param_name_abb: List[str]
    ) -> Optional[InputParameter]:
        # to original parameter name
        param_names = [TO_ORI[n] for n in param_name_abb]

        try:
            param = self._cfg[param_names[0]]
            if len(param_names) > 1:
                for param_name in param_names[1:]:
                    param = param.children[param_name]

            return param

        except KeyError:
            return None

    def set_value(
        self,
        param_name_abb: List[str],
        value: Dict
    ) -> None:
        # to original parameter name
        param_names = [TO_ORI[n] for n in param_name_abb]

        try:
            param = self._cfg[param_names[0]]
            if len(param_names) > 1:
                for param_name in param_names[1:]:
                    param = param.children[param_name]

            param.value = value

        except KeyError:
            return None

    def get_bottom_params(
        self
    ) -> List[InputParameter]:
        bottom_params = []
        for top_param in self._cfg.values():
            bottom_params += top_param.get_bottom_params()

        return bottom_params

    def remove_num_value_dict(
        self
    ) -> None:
        for top_param in self._cfg.values():
            top_param.remove_num_value_dict()
