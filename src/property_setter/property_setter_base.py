import random
from abc import ABCMeta, abstractmethod, abstractproperty
from typing import List, Union

import networkx as nx


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
