from typing import Dict, List, Union

from src.input_parameter import InputParameter


class Config():
    def __init__(
        self,
        cfg: Dict
    ) -> None:
        self._cfg = cfg

    def get_value(
        self,
        param_name: str,
        ancestors: List[str] = []
    ) -> Union[str, int, float, List]:
        if ancestors:
            root_param = ancestors.pop(0)
            param = self._cfg[root_param].get_descendant_param(
                param_name,
                ancestors
            )
        else:
            param = self._cfg[param_name]

        return param.get_value()
