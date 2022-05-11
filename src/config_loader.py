
from typing import Any, Dict, List, Union

import numpy as np

from src.format import Format


class InputParameter():
    def __init__(
        self,
        name: str,
        value: Any,
        format: Format,
        ancestor_names: List[str] = [],
    ) -> None:
        self.name = name
        self.ancestor_names = ancestor_names

        # Initialize children parameter
        self.children = {}
        if fmt_children := format.get_children(self.name,
                                               self.ancestor_names):
            if(input_children := (fmt_children & set(value.keys()))):
                for input_child in input_children:
                    self.children[input_child] = (
                        InputParameter(input_child,
                                       value[input_child],
                                       format,
                                       self.ancestor_names + [self.name])
                    )

        # bottom parameter
        elif (isinstance(value, dict)
              and isinstance(list(value.values())[0], str)):
            self.value = {k: self._convert_tuple_to_list(v)
                          for k, v in value.items()}
        else:
            self.value = value

    def _convert_tuple_to_list(
        self,
        tuple_str: str
    ) -> Union[List[int], List[float]]:
        def convert_to_num(num_str: str) -> Union[int, float]:
            temp_float = round(float(num_str), 4)
            if(temp_float.is_integer()):
                return int(temp_float)
            else:
                return temp_float

        tuple_str = tuple_str.replace('(', '')
        tuple_str = tuple_str.replace(')', '')
        tuple_str = tuple_str.replace(' ', '')

        args_dict = {'start': None, 'stop': None, 'step': None}
        for i, arg in enumerate(tuple_str.split(',')):
            if(i == 0 or 'start' in arg):
                args_dict['start'] = float(arg.replace('start=', ''))
            elif(i == 1 or 'stop' in arg):
                args_dict['stop'] = float(arg.replace('stop=', ''))
            elif(i == 2 or 'step' in arg):
                args_dict['step'] = float(arg.replace('step=', ''))

        args_dict['stop'] += args_dict['step']  # include stop

        return [convert_to_num(v) for v in np.arange(**args_dict)]


class ConfigLoader():
    def __init__(
        self,
        format: Format,
        cfg_raw: Dict
    ) -> None:
        self.parameters = {}
        for input_top_param, value in cfg_raw.items():
            self.parameters[input_top_param] = InputParameter(
                input_top_param,
                value,
                format
            )
