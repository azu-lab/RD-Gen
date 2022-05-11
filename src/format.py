import os
from typing import List, Optional, Set

import yaml


class Format:
    def __init__(
        self,
        method_name: str
    ) -> None:
        if method_name == "Layer by layer":
            format_path = (os.path.dirname(__file__)
                           + "/config_format/layer_by_layer_format.yaml")
        elif method_name == "Chain":
            format_path = (os.path.dirname(__file__)
                           + "/config_format/chain_format.yaml")
        else:
            raise NotImplementedError

        with open(format_path) as f:
            self._format = yaml.safe_load(f)

    def get_children(
        self,
        param_name: str,
        ancestor_names: Optional[List[str]]
    ) -> Optional[Set[str]]:
        if ancestor_names:
            for i, ancestor_name in enumerate(ancestor_names):
                if i == 0:
                    temp_param = self._format[ancestor_name]
                else:
                    temp_param = temp_param["Children"][ancestor_name]
            children = temp_param["Children"][param_name].get("Children")
        else:
            children = self._format[param_name].get("Children")

        if children:
            return set(children.keys())
        else:
            return None
