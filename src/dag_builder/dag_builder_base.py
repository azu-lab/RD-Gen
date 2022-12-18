from abc import ABCMeta, abstractmethod
from typing import Generator, List

import networkx as nx

from ..common import Util
from ..config import Config


class DAGBuilderBase(metaclass=ABCMeta):
    """DAG builder base class."""

    def __init__(self, config: Config, max_try: int = 100) -> None:
        """Constructor.

        Parameters
        ----------
        config : Config
            Config.
        max_try : int, optional
            Maximum number of DAG build attempts with the same parameters, by default 100

        """
        self.validate_config(config)
        self._config = config
        self._max_try = max_try

    @abstractmethod
    def build(self) -> Generator[nx.DiGraph, None, None]:
        raise NotImplementedError

    @abstractmethod
    def validate_config(self, config: Config):
        raise NotImplementedError

    @staticmethod
    def _add_minimum_edges(src_layer: List[int], tgt_layer: List[int], G: nx.DiGraph) -> None:
        """Add minimum edges

        Connects the source and target layers with a minimum number of edges.
        The function terminates
        when the out-degree of the source layer is greater than or equal to 1
        and the in-degree of the target layer is greater than or equal to 1.

        Parameters
        ----------
        src_layer : List[int]
            Indices of nodes that are the source of the edge.
        tgt_layer : List[int]
            Indices of nodes that are the target of the edge.
        G : nx.DiGraph
            DAG.

        """

        def is_finish() -> bool:
            for src_node_i in src_layer:
                if G.out_degree(src_node_i) == 0:
                    return False
            for tgt_node_i in tgt_layer:
                if G.in_degree(tgt_node_i) == 0:
                    return False

            return True

        while not is_finish():
            min_out_src_i = Util.get_min_out_node(G, src_layer)
            min_in_tgt_i = Util.get_min_in_node(G, tgt_layer)
            G.add_edge(min_out_src_i, min_in_tgt_i)

    @staticmethod
    def _ensure_weakly_connected(G: nx.DiGraph) -> None:
        """Ensure weakly connected.

        Connect the separated DAGs into one,
        without changing the number of entry and exit nodes.

        Parameters
        ----------
        G : nx.DiGraph
            DAG.

        """

        comps = list(nx.weakly_connected_components(G))
        if len(comps) == 1:
            return None

        comps.sort(key=lambda x: len(x))
        tgt_comp = comps.pop(-1)  # Most big component

        entry_nodes = set(Util.get_entry_nodes(G))
        exit_nodes = set(Util.get_exit_nodes(G))
        for src_comp in comps:
            src_option = src_comp - exit_nodes
            tgt_option = tgt_comp - entry_nodes
            src_i = Util.get_min_out_node(G, src_option)
            tgt_i = Util.get_min_in_node(G, tgt_option)
            G.add_edge(src_i, tgt_i)
