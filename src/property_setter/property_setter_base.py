import random
import sys
from abc import ABCMeta, abstractmethod
from typing import List, Union

import networkx as nx
from src.exceptions import MaxBuildFailError


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
