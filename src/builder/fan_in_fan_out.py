
import copy
import random
from logging import getLogger
from typing import Generator, Tuple

import networkx as nx
from src.builder.dag_builder_base import DAGBuilderBase
from src.config import Config
from src.exceptions import MaxBuildFailError

logger = getLogger(__name__)


class FanInFanOutBuilder(DAGBuilderBase):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        super().__init__(cfg)
        self._max_build_fail = 10000  # HACK

        # Set bound
        out_degree = self._cfg.get_value('OD')
        self._max_out = self.get_bound("max", out_degree)
        in_degree = self._cfg.get_value('ID')
        self._max_in = self.get_bound("max", in_degree)
        num_nodes = self._cfg.get_value('NN')
        self._min_num_nodes = self.get_bound("min", num_nodes)
        self._max_num_nodes = self.get_bound("max", num_nodes)

    def _get_max_diff_node(
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

    def _force_merge_to_exit_nodes(  # HACK
        self,
        num_exit: int,
        G: nx.DiGraph
    ) -> None:
        leaves = [v for v, d in G.out_degree() if d == 0]
        exit_nodes_i = []
        for _ in range(num_exit):
            exit_nodes_i.append(G.number_of_nodes())
            G.add_node(G.number_of_nodes())

        if(len(leaves) > len(exit_nodes_i)):
            no_in_degree_i = copy.deepcopy(exit_nodes_i)
            for leaf in leaves:
                if(no_in_degree_i):
                    exit_node_i = random.choice(no_in_degree_i)
                    G.add_edge(leaf, exit_node_i)
                    no_in_degree_i.remove(exit_node_i)
                else:
                    G.add_edge(leaf, random.choice(exit_nodes_i))
        else:
            while(exit_nodes_i):
                for leaf in leaves:
                    if(not exit_nodes_i):
                        break
                    exit_node_i = random.choice(exit_nodes_i)
                    G.add_edge(leaf, exit_node_i)
                    exit_nodes_i.remove(exit_node_i)

    def build(self) -> Generator[nx.DiGraph, None, None]:
        for _ in range(self._cfg.get_value('NG')):
            num_build_fail = 0
            G = nx.DiGraph()

            # Determine number_of_nodes bound (Loop finish condition)
            num_exit = self._cfg.get_value('NEX', ['FME'])
            if num_exit:
                num_exit = self.random_choice(num_exit)
                lower = self._min_num_nodes - num_exit
                upper = self._max_num_nodes - num_exit
            else:
                lower = self._min_num_nodes
                upper = self._max_num_nodes

            while not (lower <= G.number_of_nodes() <= upper):
                # Add entry nodes
                num_entry = self._cfg.get_value('NEN')
                for i in range(self.random_choice(num_entry)):
                    G.add_node(G.number_of_nodes())

                if self.get_random_bool():
                    # Fan-out
                    max_diff_node_i, diff = self._get_max_diff_node(G)
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
                if G.number_of_nodes() > self._max_num_nodes:
                    num_build_fail += 1
                    if num_build_fail == self._max_build_fail:
                        msg = ("A DAG satisfying 'Number of nodes' "
                               "could not be built "
                               f"in {self._max_build_fail} tries.")
                        raise MaxBuildFailError(msg)
                    else:
                        G = nx.DiGraph()  # reset

            # Add exit nodes (Optional)
            if num_exit:
                self._force_merge_to_exit_nodes(num_exit, G)

            yield G
