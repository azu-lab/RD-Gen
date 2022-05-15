import random
from abc import ABCMeta, abstractmethod, abstractproperty
from typing import Union

import networkx as nx


class PropertySetterBase(metaclass=ABCMeta):
    @abstractproperty
    def choices(self):
        raise NotImplementedError

    @abstractmethod
    def set(
        self,
        G: nx.DiGraph
    ) -> None:
        raise NotImplementedError

    def choice_one(
        self,
    ) -> Union[int, float]:
        if isinstance(self.choices, list):
            return random.choice(self.choices)
        else:
            return self.choices
