from typing import Any, List, Optional, Union

import numpy as np

from src.abbreviation import TO_ABB

NOT_PARAM_NAME = {"fixed", "random", "combination"}


class InputParameter():
    def __init__(
        self,
        name: str,
        value: Any,
        parent: Optional['InputParameter'] = None
    ) -> None:
        self.name = name
        self.parent = parent

        # Initialize children
        self.children = {}
        if self._has_child(value):
            for child_name, value in value.items():
                self.children[child_name.lower()] = (
                    InputParameter(
                        child_name.lower(),
                        value,
                        self
                    ))

        # Initialize value
        elif (isinstance(value, dict)
              and list(value.keys())[0].lower() in NOT_PARAM_NAME
              and isinstance(list(value.values())[0], str)):
            self.value = {k: self._convert_tuple_to_list(v)
                          for k, v in value.items()}
        elif isinstance(value, str):
            self.value = value.lower()
        else:
            self.value = value

    def get_child_value(
        self,
        child_name: str
    ):
        try:
            return self.children[child_name].value
        except KeyError:
            return None

    def _has_child(
        self,
        value: Any
    ) -> bool:
        if isinstance(value, dict):
            if set(k.lower() for k in value.keys()) - NOT_PARAM_NAME:
                return True
            else:
                return False
        else:
            return False

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

    def remove_num_value_dict(
        self
    ) -> None:
        if self.children:
            for child in self.children.values():
                child.remove_num_value_dict()
        elif isinstance(self.value, dict):
            self.value = list(self.value.values())[0]

    def get_bottom_params(
        self
    ) -> List['InputParameter']:
        if not self.children:
            return [self]

        bottom_params = []
        for child in self.children.values():
            bottom_params += child.get_bottom_params()

        return bottom_params

    def get_family_tree_abb(
        self
    ) -> List[str]:
        family_tree = [TO_ABB[self.name]]
        if self.parent:
            family_tree = self.parent.get_family_tree_abb() + family_tree

        return family_tree
