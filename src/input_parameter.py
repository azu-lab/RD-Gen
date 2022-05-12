from typing import Any, List, Optional, Union

import numpy as np

from src.config_format.format import Format
from src.exceptions import InvalidArgumentError


class InputParameter():
    def __init__(
        self,
        name: str,
        value: Any,
        format: Format,
        ancestors: List[str] = [],
    ) -> None:
        self.name = name
        self.ancestors = ancestors

        # Initialize children parameter
        self.children = {}
        if fmt_children := format.get_children(self.name,
                                               self.ancestors):
            if(input_children := (fmt_children & set(value.keys()))):
                for input_child in input_children:
                    self.children[input_child] = (
                        InputParameter(input_child,
                                       value[input_child],
                                       format,
                                       self.ancestors + [self.name])
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
        converted = [convert_to_num(v) for v in np.arange(**args_dict)]

        # HACK: if type is float, remove stop value
        for v in converted:
            if isinstance(v, float):
                del converted[-1]
                break

        return converted

    def get_descendant_param(
        self,
        param_name: str,
        middle_params: List[str] = []
    ) -> 'InputParameter':
        """
        Args:
            param_name: target parameter name
            middle_params (List[str]): root parameter -> [THIS ARG] -> target parameter (Optional)
        """
        if not self.children:
            raise InvalidArgumentError

        if middle_params:
            for i, middle_param in enumerate(middle_params):
                if i == 0:
                    param = self.children[middle_param]
                else:
                    param = param.children[middle_param]
            param = param.children[param_name]
        else:
            param = self.children[param_name]

        return param

    def get_value(
        self,
    ) -> Union[str, int, float, List]:
        if isinstance(self.value, dict):
            return list(self.value.values())[0]
        else:
            return self.value
