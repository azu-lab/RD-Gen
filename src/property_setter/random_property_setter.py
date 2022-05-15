from typing import List, Union

import networkx as nx
from src.property_setter.property_setter_base import PropertySetterBase


class RandomPropertySetter(PropertySetterBase):
    def __init__(
        self,
        property_name: str,
        choices: Union[int, float, List],
        target: str
    ) -> None:
        self._property_name = property_name
        self.choices = choices
        self._target = target

    @property
    def choices(self):
        return self._choices

    @choices.setter
    def choices(
        self,
        choices: Union[int, float, List]
    ):
        self._choices = choices

    def set(
        self,
        G: nx.DiGraph
    ) -> None:
        if self._target == "node":
            for node_i in G.nodes():
                G.nodes[node_i][self._property_name] = \
                    self.choice_one()
        else:
            for src_i, tgt_i in G.edges():
                G.edges[src_i, tgt_i][self._property_name] = \
                    self.choice_one()
