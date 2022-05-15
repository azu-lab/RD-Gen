from typing import List

import networkx as nx
from src.input_parameter import InputParameter
from src.property_setter.property_setter_base import PropertySetterBase


class PeriodSetter(PropertySetterBase):
    def __init__(
        self,
        base_param: InputParameter
    ) -> None:
        self._type = base_param.get_child_value("periodic type")
        self._choices = base_param.get_child_value("period")
        self._entry_choices = base_param.get_child_value("entry node period")
        self._exit_choices = base_param.get_child_value("exit node period")

    def _random_set(
        self,
        nodes: List[int],
        choices: List[int],
        G: nx.DiGraph
    ) -> None:
        for node_i in nodes:
            G.nodes[node_i]["Period"] = self.choice_one(choices)

    def set(
        self,
        G: nx.DiGraph
    ) -> None:
        entry_set_flag = False
        exit_set_flag = False

        if self._type == "all":
            self._random_set(list(G.nodes()),
                             self._choices,
                             G)
        elif self._type == "io":
            entry_set_flag = True
            exit_set_flag = True
        elif self._type == "entry":
            entry_set_flag = True
        elif self._type == "chain":
            pass  # TODO

        if self._entry_choices:
            entry_set_flag = True
        if self._exit_choices:
            exit_set_flag = True

        if entry_set_flag:
            entry_nodes = [v for v, d in G.in_degree() if d == 0]
            self._random_set(entry_nodes,
                             self._entry_choices,
                             G)
        if exit_set_flag:
            exit_nodes = [v for v, d in G.out_degree() if d == 0]
            self._random_set(exit_nodes,
                             self._exit_choices,
                             G)
