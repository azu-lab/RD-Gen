import networkx as nx
import numpy as np
from src.config import Config
from src.property_setter.property_setter_base import PropertySetterBase


class CCRSetter(PropertySetterBase):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        self._CCR_choices = cfg.get_value(["PP", "CCR"])

    def set(
        self,
        G: nx.DiGraph
    ) -> None:
        ccr = self.choice_one(self._CCR_choices)

        # Calculate sum of execution time
        sum_exec = 0
        for node_i in G.nodes():
            sum_exec += G.nodes[node_i]["Execution_time"]

        sum_comm = ccr * sum_exec

        # Set communication time
        comm_grouping = self._fast_grouping(sum_comm, G.number_of_edges())
        for edge, comm in zip(G.edges(), comm_grouping):
            int_comm = int(np.floor(comm))
            if int_comm == 0:
                int_comm = 1
            G.edges[edge[0], edge[1]]['Communication_time'] = int_comm
