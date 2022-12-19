import random
from abc import ABCMeta, abstractmethod
from logging import getLogger
from typing import List, Optional

import networkx as nx

from ..config import Config

logger = getLogger(__name__)


class PropertySetterBase(metaclass=ABCMeta):
    def __init__(self, config: Config) -> None:
        self._validate_config(config)
        self._config = config

    @abstractmethod
    def set(self, dag: nx.DiGraph) -> None:
        raise NotImplementedError

    @abstractmethod
    def _validate_config(self, config: Config) -> None:
        raise NotImplementedError

    @staticmethod
    def _grouping(sum: int, num_groups: int) -> Optional[List[int]]:
        # Check feasibility
        if (sum / num_groups) < 1.0:
            return None  # Infeasible

        groups = [[0 for _ in range(sum)]]
        for _ in range(num_groups - 1):
            random.shuffle(groups)
            choose_group = groups.pop(0)
            while len(choose_group) == 1:
                groups.append(choose_group)
                choose_group = groups.pop(0)

            if len(choose_group) == 2:
                groups.append([choose_group[0]])
                groups.append([choose_group[-1]])
            else:
                rand_idx = random.randint(1, len(choose_group) - 2)
                groups.append(choose_group[:rand_idx])
                groups.append(choose_group[rand_idx:])

        return [len(group) for group in groups]

    @staticmethod
    def _output_round_up_warning(round_up_param: str, error_param: str) -> None:
        logger.warning(
            f"'{round_up_param}' is rounded up to 1 because it is very small."
            f"This rounding up may cause errors in '{error_param}'."
            "To prevent this error, it is recommended to use a smaller unit"
            "(e.g., change 10 ms to 10000 ns)."
        )
