import random
from abc import ABCMeta, abstractmethod
from typing import Generator, List, Union

import networkx as nx
from src.config import Config
from src.exceptions import InvalidArgumentError


class DAGBuilderBase(metaclass=ABCMeta):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        self._cfg = cfg

    @abstractmethod
    def build(self) -> Generator[nx.DiGraph, None, None]:
        raise NotImplementedError

    def random_choice(
        self,
        param_value: Union[int, float, List]
    ) -> Union[int, float]:
        if not param_value:
            raise InvalidArgumentError

        if isinstance(param_value, list):
            choose_value = random.choice(param_value)
        else:
            choose_value = param_value

        return choose_value

    def get_bound(
        self,
        max_or_min: str,
        param_value: Union[int, float, List]
    ) -> Union[int, float]:
        if not param_value:
            raise InvalidArgumentError

        if isinstance(param_value, list):
            if max_or_min == "max":
                bound = max(param_value)
            elif max_or_min == "min":
                bound = min(param_value)
            else:
                raise InvalidArgumentError()
        else:
            bound = param_value

        return bound

    def get_random_bool(
        self
    ) -> bool:
        random_int = random.randint(1, 10)
        if random_int <= 5:
            return True
        else:
            return False
