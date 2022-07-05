import random
import sys
from abc import ABCMeta, abstractmethod
from typing import List, Union

import networkx as nx
import numpy as np
from src.exceptions import InvalidArgumentError, MaxBuildFailError


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
            rand_idx = random.randint(1, len(choose_group)-2)
            groups.append(choose_group[:rand_idx])
            groups.append(choose_group[rand_idx:])

        return [len(group) for group in groups]

    def _fast_grouping(
        self,
        sum_value: float,
        num_group: int,
        upper_bound: float = None
    ) -> List[float]:
        if upper_bound:  # HACK
            if sum_value / num_group >= upper_bound:  # HACK
                raise MaxBuildFailError

            while True:
                grouping = [0.0]*num_group
                sum = sum_value
                for i in range(1, num_group):
                    next_sum = - sys.maxsize
                    while(sum - next_sum >= upper_bound):
                        next_sum = sum * (random.uniform(0, 1)
                                          ** (1/(num_group-i)))
                    grouping[i-1] = sum - next_sum
                    sum = next_sum
                if sum < upper_bound:
                    grouping[num_group-1] = sum
                    break
        else:
            grouping = [0]*num_group
            sum = sum_value
            for i in range(1, num_group):
                next_sum = sum * (random.uniform(0, 1)**(1/(num_group-i)))
                grouping[i-1] = sum - next_sum
                sum = next_sum
                grouping[num_group-1] = sum

        return grouping
