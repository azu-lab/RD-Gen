from typing import Dict, List, Optional, Union

from src.abbreviation import TO_ABB, TO_ORI


class Config():
    def __init__(
        self,
        cfg: Dict
    ) -> None:
        self._cfg = cfg

    def get_value(
        self,
        param_name_abb: str,
        ancestors_abb: List[str] = []
    ) -> Optional[Union[str, int, float, List]]:
        # to original parameter name
        param_name = TO_ORI[param_name_abb]
        ancestors = [TO_ORI[a] for a in ancestors_abb]

        try:
            # get param
            if ancestors:
                root_param = ancestors.pop(0)
                param = self._cfg[root_param].get_descendant_param(
                    param_name,
                    ancestors
                )
            else:
                param = self._cfg[param_name]

            return param.get_value()

        except KeyError:
            return None
