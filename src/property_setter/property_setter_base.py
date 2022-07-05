import random
from abc import ABCMeta, abstractmethod
from typing import List, Union

import networkx as nx
from src.exceptions import InvalidArgumentError


class PropertySetterBase(metaclass=ABCMeta):
    @abstractmethod
    def set(
        self,
        G: nx.DiGraph
    ) -> None:
        raise NotImplementedError

    def choice_one(
        self,
        choices: Union[int, float, List]
    ) -> Union[int, float]:
        if isinstance(choices, list):
            return random.choice(choices)
        else:
            return choices

    @staticmethod
    def _grouping_int(
        sum_value: int,
        num_group: int
    ) -> List[int]:
        # validate
        if (sum_value / num_group) < 1.0:
            raise InvalidArgumentError('(sum_value/num_group) < 1.0')

        groups = [[0 for _ in range(sum_value)]]
        for _ in range(num_group-1):
            random.shuffle(groups)
            choose_group = groups.pop(0)
            while len(choose_group) == 1:
                groups.append(choose_group)
                choose_group = groups.pop(0)

            if len(choose_group) == 2:
                groups.append([choose_group[0]])
                groups.append([choose_group[-1]])
            else:
                rand_idx = random.randint(1, len(choose_group)-2)
                groups.append(choose_group[:rand_idx])
                groups.append(choose_group[rand_idx:])

        return [len(group) for group in groups]
