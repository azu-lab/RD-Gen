import random
from typing import List, Optional, Union

import networkx as nx
import numpy as np
from src.config import Config
from src.property_setter.period_setter import PeriodSetter
from src.property_setter.property_setter_base import PropertySetterBase


class EPUSetter(PropertySetterBase):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        self._E_choices = cfg.get_value(["PP", "ET"])
        if base_param := cfg.get_param(["PP", "MP"]):
            self._period_setter = PeriodSetter(base_param)
        else:
            self._period_setter = None
        self._U_choices = cfg.get_value(["PP", "MP", "TU"])

    def _UUniFast(
        self,
        G: nx.DiGraph,
        total_U: float
    ) -> None:
        n = G.number_of_nodes()
        sum_U = total_U
        for i in range(1, n):
            next_sum_U = sum_U * (random.uniform(0, 1)**(1/(n-i)))
            G.nodes[i-1]["Utilization"] = sum_U - next_sum_U
            sum_U = next_sum_U
        G.nodes[n-1]["Utilization"] = sum_U

    def set(
        self,
        G: nx.DiGraph
    ) -> None:
        if self._U_choices:
            # Set utilization
            total_U = self.choice_one(self._U_choices)
            self._UUniFast(G, total_U)

            # Set period
            self._period_setter.set(G)

            # Set execution time (E = U * P)
            for node_i in G.nodes():
                exec = int(np.floor(
                    G.nodes[node_i]["Utilization"] * G.nodes[node_i]["Period"]
                ))
                if exec == 0:
                    exec = 1
                G.nodes[node_i]["Execution time"] = exec

        else:
            if self._period_setter:
                self._period_setter.set(G)
            if self._E_choices:
                for node_i in G.nodes():
                    G.nodes[node_i]["Execution time"] = \
                        self.choice_one(self._E_choices)
