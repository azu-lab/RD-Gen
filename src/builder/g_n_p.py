
import random
from typing import Generator

import networkx as nx
from src.builder.dag_builder_base import DAGBuilderBase
from src.config import Config


class GNPBuilder(DAGBuilderBase):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        super().__init__(cfg)
        self._num_nodes = self._cfg.get_value(["GS", "NN"])
        self._edge_prob = self._cfg.get_value(["GS", "PE"])

    def build(self) -> Generator[nx.DiGraph, None, None]:
        for _ in range(self._cfg.get_value(["NG"])):
            # Determine number_of_nodes
            num_nodes = self.random_choice(self._num_nodes)
            num_exit = self._cfg.get_value(["GS", "NEX"])
            num_entry = self._cfg.get_value(["GS", "NEN"])
            if num_exit:
                num_exit = self.random_choice(num_exit)
                num_nodes -= num_exit
            if num_entry:
                num_entry = self.random_choice(num_entry)
                num_nodes -= num_entry

            # Initialize DAG
            G = nx.DiGraph()
            for i in range(num_nodes):
                G.add_node(G.number_of_nodes())

            # Add edge
            prob_edge = self.random_choice(self._edge_prob)
            for i in range(num_nodes):
                for j in range(num_nodes):
                    if (random.randint(1, 100) < prob_edge * 100
                            and i < j):
                        G.add_edge(i, j)

            # Add entry nodes (Optional)
            if num_entry:
                roots = [v for v, d in G.in_degree() if d == 0]
                entry_nodes_i = []
                for _ in range(num_entry):
                    entry_nodes_i.append(G.number_of_nodes())
                    G.add_node(G.number_of_nodes())
                self._add_min_edges(roots, entry_nodes_i, G)

            # Add exit nodes (Optional)
            if num_exit:
                leaves = [v for v, d in G.out_degree() if d == 0]
                exit_nodes_i = []
                for _ in range(num_exit):
                    exit_nodes_i.append(G.number_of_nodes())
                    G.add_node(G.number_of_nodes())
                self._add_min_edges(leaves, exit_nodes_i, G)

            yield G
