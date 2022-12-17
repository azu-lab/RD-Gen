import copy
import itertools
from typing import Generator, List, Tuple, Union

from src.abbreviation import TO_ABB, TO_ORI
from src.config import Config
from src.input_parameter import InputParameter


class ComboGenerator():
    def __init__(
            self,
            combo_cfg: Config
    ) -> None:
        self._combo_cfg = combo_cfg
        self._combo_params: List[InputParameter] = []
        self._combo_values: List[Union[List[int], List[float]]] = []
        self._search_combo()

    def _search_combo(self) -> None:
        bottom_params = self._combo_cfg.get_bottom_params()
        for bottom_param in bottom_params:
            if (isinstance(bottom_param.value, dict)
                    and list(bottom_param.value.keys())[0] == "Combination"):
                self._combo_params.append(bottom_param)
                self._combo_values.append(list(bottom_param.value.values())[0])

    def _create_combo_dir_name(
        self,
        index: int,
        combo: List[Union[int, float]]
    ) -> str:
        combo_dir_name = None
        naming = self._combo_cfg.get_value(["OF", "NCD"])
        if naming == 'full spell':
            for param, value in zip(self._combo_params, combo):
                param_str_list = param.name[1].split(' ')
                param_str_list = [s.capitalize() for s in param_str_list]
                if(combo_dir_name):
                    combo_dir_name += f'_{"".join(param_str_list)}_{value}'
                else:
                    combo_dir_name = f'{"".join(param_str_list)}_{value}'

        elif naming == 'abbreviation':
            for param, value in zip(self._combo_params, combo):
                try:
                    param = TO_ABB[param.name]
                except KeyError:  # Additional parameter
                    TO_ABB[param.name] = param.name  # HACK
                    TO_ORI[param.name] = param.name  # HACK
                    param = param.name

                if(combo_dir_name):
                    combo_dir_name += f'_{param}_{value}'
                else:
                    combo_dir_name = f'{param}_{value}'

        elif naming == 'index of combination':
            combo_dir_name = f'combination_{index}'

        else:
            raise NotImplementedError

        return combo_dir_name

    def _create_cfg(
        self,
        combo: List[Union[int, float]]
    ) -> Config:
        cfg = copy.deepcopy(self._combo_cfg)
        for combo_param, combo_value in zip(self._combo_params, combo):
            family_tree = combo_param.get_family_tree_abb()
            cfg.set_value(family_tree, {"Fixed": combo_value})
        cfg.remove_num_value_dict()

        return cfg

    def get_num_combos(self) -> int:
        return len(list(itertools.product(*self._combo_values)))

    def generate(
        self
    ) -> Tuple[Generator, Generator, Generator]:
        all_combo = list(itertools.product(*self._combo_values))
        for i, combo in enumerate(all_combo):
            all_combo_dir_name = self._create_combo_dir_name(i, combo)
            all_combo_log = {k.name: v for k, v
                             in zip(self._combo_params, combo)}
            all_combo_cfg = self._create_cfg(combo)

            yield (all_combo_dir_name, all_combo_log, all_combo_cfg)
