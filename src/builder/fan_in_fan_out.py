
import copy
import random
from typing import Generator, Tuple

import networkx as nx
from src.builder.dag_builder_base import DAGBuilderBase
from src.config import Config
from src.exceptions import MaxBuildFailError


class FanInFanOutBuilder(DAGBuilderBase):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        super().__init__(cfg)
        self._max_build_fail = 10000  # HACK

        # Set bound
        out_degree = self._cfg.get_value(["GS", "OD"])
        self._max_out = self.get_bound("max", out_degree)
        in_degree = self._cfg.get_value(["GS", "ID"])
        self._max_in = self.get_bound("max", in_degree)

    def _get_max_out_diff_node(
        self,
        G: nx.DiGraph
    ) -> Tuple[int, int]:
        """
        Find the node with the biggest difference
        between its out-degree and max value of "out-degree".

        Search by smallest index first.

        Returns:
            Index of nodes matching the condition (int)
        """
        search_log = {"max_diff": 0,
                      "max_diff_node_i": None}
        for node_i in G.nodes():
            out = G.out_degree(node_i)
            if out == 0:
                return node_i, self._max_out
            else:
                diff = self._max_out - out
                if diff > search_log["max_diff"]:
                    search_log["max_diff"] = diff
                    search_log["max_diff_node_i"] = node_i

        return search_log["max_diff_node_i"], search_log["max_diff"]

    def _init_dag(
        self,
        num_entry
    ) -> nx.DiGraph:
        G = nx.DiGraph()
        for _ in range(num_entry):
            G.add_node(G.number_of_nodes())

        return G

    def build(self) -> Generator[nx.DiGraph, None, None]:
        for _ in range(self._cfg.get_value(["NG"])):
            num_build_fail = 0

            # Determine number_of_nodes (Loop finish condition)
            num_nodes = self.random_choice(self._cfg.get_value(["GS", "NN"]))
            if num_exit := self._cfg.get_value(["GS", "NEX"]):
                num_nodes -= self.random_choice(num_exit)
            num_entry = self.random_choice(self._cfg.get_value(["GS", "NEN"]))
            num_nodes -= num_entry

            G = self._init_dag(num_entry)

            while G.number_of_nodes() != num_nodes:
                if self.get_random_bool():
                    # Fan-out
                    max_diff_node_i, diff = self._get_max_out_diff_node(G)
                    num_add = random.randint(1, diff)
                    add_node_i_list = [G.number_of_nodes() + i
                                       for i in range(num_add)]
                    nx.add_star(G, [max_diff_node_i] + add_node_i_list)

                else:
                    # Fan-in
                    num_sources = random.randint(1, self._max_in)
                    nodes = list(G.nodes())
                    random.shuffle(nodes)
                    sources = []
                    for node_i in nodes:
                        if G.out_degree(node_i) < self._max_out:
                            sources.append(node_i)
                            if len(sources) == num_sources:
                                break

                    add_node_i = G.number_of_nodes()
                    G.add_node(add_node_i)
                    for source_node_i in sources:
                        G.add_edge(source_node_i, add_node_i)

                # Check build fail
                if G.number_of_nodes() > num_nodes:
                    num_build_fail += 1
                    if num_build_fail == self._max_build_fail:
                        msg = ("A DAG satisfying 'Number of nodes' "
                               "could not be built "
                               f"in {self._max_build_fail} tries.")
                        raise MaxBuildFailError(msg)
                    else:
                        G = self._init_dag(num_entry)  # reset

            # Add exit nodes (Optional)
            if num_exit:
                leaves = [v for v, d in G.out_degree() if d == 0]
                exit_nodes_i = []
                for _ in range(num_exit):
                    exit_nodes_i.append(G.number_of_nodes())
                    G.add_node(G.number_of_nodes())
                self._add_min_edges(leaves, exit_nodes_i, G)

            # Ensure weakly connected (Optional)
            if (self._cfg.get_value(["GS", "EWC"])):
                self.ensure_weakly_connected(G)

            yield G
