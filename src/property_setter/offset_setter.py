from typing import List, Union

import networkx as nx
from src.property_setter.property_setter_base import PropertySetterBase


class OffsetSetter(PropertySetterBase):
    def __init__(
        self,
        choices: Union[int, float, List]
    ) -> None:
        self._choices = choices

    def set(
        self,
        G: nx.DiGraph
    ) -> None:
        for node_i in G.nodes():
            if 'Period' in G.nodes[node_i].keys():
                G.nodes[node_i]['Offset'] = \
                    self.choice_one(self._choices)
