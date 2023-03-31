from abc import ABCMeta, abstractmethod
from typing import Generator, List

import networkx as nx

from ..common import Util
from ..config import Config
from ..exceptions import BuildFailedError


class DAGBuilderBase(metaclass=ABCMeta):
    """DAG builder base class."""

    def __init__(self, config: Config, max_try: int = 100) -> None:
        """Constructor.

        Parameters
        ----------
        config : Config
            Config.
        max_try : int, optional
            Maximum number of build attempts for a single DAG, by default 100

        """
        self._validate_config(config)
        self._config = config
        self._max_try = max_try

    @abstractmethod
    def build(self) -> Generator[nx.DiGraph, None, None]:
        raise NotImplementedError

    @abstractmethod
    def _validate_config(self, config: Config):
        raise NotImplementedError

    @staticmethod
    def _force_create_source_nodes(G: nx.DiGraph, number_of_source_nodes: int) -> None:
        """Create an source node forcibly.

        Add 'number_of_source_nodes' number of new nodes to the DAG
        and make them source nodes.
        All original source nodes are connected to the newly added node.

        Parameters
        ----------
        G : nx.DiGraph
            DAG.
        number_of_source_nodes : int
            Number of source nodes.

        """
        original_entries = Util.get_source_nodes(G)
        new_entries = [G.number_of_nodes() + i for i in range(number_of_source_nodes)]
        G.add_nodes_from(new_entries)
        DAGBuilderBase._add_minimum_edges(new_entries, original_entries, G)

    @staticmethod
    def _force_create_exit_nodes(G: nx.DiGraph, number_of_exit_nodes: int) -> None:
        """Create an sink node forcibly.

        Add 'number_of_exit_nodes' number of new nodes to the DAG
        and make them sink nodes.
        All original sink nodes are connected to the newly added node.

        Parameters
        ----------
        G : nx.DiGraph
            DAG.
        number_of_exit_nodes : int
            Number of sink nodes.

        """
        original_exits = Util.get_exit_nodes(G)
        new_exits = [G.number_of_nodes() + i for i in range(number_of_exit_nodes)]
        G.add_nodes_from(new_exits)
        DAGBuilderBase._add_minimum_edges(original_exits, new_exits, G)

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
    def _ensure_weakly_connected(G: nx.DiGraph, keep_num_entry: bool, keep_num_exit: bool) -> None:
        """Ensure weakly connected.

        Parameters
        ----------
        G : nx.DiGraph
            DAG.
        keep_num_entry : bool
            Keep the number of source nodes.
        keep_num_exit : bool
            Keep the number of sink nodes.

        Raises
        ------
        BuildFailedError
            The number of source nodes and the number of sink nodes
            cannot be kept because of the size 1 component.

        """
        comps = list(nx.weakly_connected_components(G))
        if len(comps) == 1:
            return None

        comps.sort(key=lambda x: len(x))
        tgt_comp = comps.pop(-1)  # Most big component

        source_nodes = set(Util.get_source_nodes(G))
        exit_nodes = set(Util.get_exit_nodes(G))
        if keep_num_entry and keep_num_exit and (source_nodes & exit_nodes):
            raise BuildFailedError(
                "The number of source nodes and the number of sink nodes"
                "cannot be maintained because of the size 1 component."
            )
        for src_comp in comps:
            src_option = src_comp - exit_nodes if keep_num_exit else src_comp
            tgt_option = tgt_comp - source_nodes if keep_num_entry else tgt_comp
            src_i = Util.get_min_out_node(G, src_option)
            tgt_i = Util.get_min_in_node(G, tgt_option)
            G.add_edge(src_i, tgt_i)
