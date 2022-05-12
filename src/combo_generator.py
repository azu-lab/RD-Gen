import copy
import itertools
from typing import Dict, Generator, List, Tuple, Union

from src.abbreviation import ToA
from src.config import Config
from src.input_parameter import InputParameter


class ComboGenerator():
    def __init__(
            self,
            combo_cfg: Dict
    ) -> None:
        self._combo_cfg = combo_cfg
        self._combo_params = []
        self._combo_values = []
        self._search_combo()

    def _search_combo(self) -> None:
        def recursive_search(param: InputParameter):
            if param.children:
                for child in param.children.values():
                    recursive_search(child)
            elif(isinstance(param.value, dict)
                 and (combo_value := param.value.get("Combination"))):
                self._combo_params.append((param.ancestors, param.name))
                self._combo_values.append(combo_value)

        for in_top_param in self._combo_cfg.values():
            recursive_search(in_top_param)

    def _create_combo_dir_name(
        self,
        index: int,
        combo: List[Union[int, float]]
    ) -> str:
        combo_dir_name = None
        if(self._combo_cfg['Naming of combination directory'].value
           == 'Full spell'):
            for param_name, value in zip(self._combo_params, combo):
                param_str_list = param_name[1].split(' ')
                param_str_list = [s.capitalize() for s in param_str_list]
                if(combo_dir_name):
                    combo_dir_name += f'_{"".join(param_str_list)}_{value}'
                else:
                    combo_dir_name = f'{"".join(param_str_list)}_{value}'

        elif(self._combo_cfg['Naming of combination directory'].value
             == 'Abbreviation'):
            for param_name, value in zip(self._combo_params, combo):
                param_name = ToA[param_name[1]]
                if(combo_dir_name):
                    combo_dir_name += f'_{param_name}_{value}'
                else:
                    combo_dir_name = f'{param_name}_{value}'

        elif(self._combo_cfg['Naming of combination directory'].value
             == 'Index of combination'):
            combo_dir_name = f'combination_{index}'

        else:
            raise NotImplementedError

        return combo_dir_name

    def _create_cfg(
        self,
        combo: List[Union[int, float]]
    ) -> Config:
        def replace_combo_to_fix(
            cfg: Dict,
            param_name: Tuple,
            fixed_value: Union[int, float]
        ) -> None:
            if ancestors := param_name[0]:
                for i, ancestor in enumerate(ancestors):
                    if i == 0:
                        ancestor_param = cfg[ancestor]
                    else:
                        ancestor_param = ancestor_param.children[ancestor]
                param = ancestor_param.children[param_name[1]]
                param.value = {"Fixed": fixed_value}
            else:
                cfg[param_name[1]].value = {"Fixed": fixed_value}

        cfg = copy.deepcopy(self._combo_cfg)
        for combo_param, value in zip(self._combo_params, combo):
            replace_combo_to_fix(cfg, combo_param, value)

        return Config(cfg)

    def generate(
        self
    ) -> Tuple[Generator, Generator, Generator]:
        all_combo = list(itertools.product(*self._combo_values))
        for i, combo in enumerate(all_combo):
            all_combo_dir_name = self._create_combo_dir_name(i, combo)
            all_combo_log = {k[1]: v for k, v
                             in zip(self._combo_params, combo)}
            all_combo_cfg = self._create_cfg(combo)

            yield (all_combo_dir_name, all_combo_log, all_combo_cfg)
