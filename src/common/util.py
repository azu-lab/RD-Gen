import random
import sys
from typing import Any, Collection, List, Optional, Union

import networkx as nx


class Util:
    """Utilization class."""

    @staticmethod
    def ambiguous_equals(s: str, comparison: str) -> bool:
        return s.lower().replace(" ", "") == comparison.lower().replace(" ", "")

    @staticmethod
    def convert_to_property(param_name: str) -> str:
        return param_name.lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def random_choice(target: Union[Any, list]):
        if isinstance(target, list):
            return random.choice(target)
        else:
            return target

    @staticmethod
    def true_or_false() -> bool:
        if random.choice([0, 1]) == 1:
            return True
        else:
            return False

    @staticmethod
    def get_source_nodes(dag: nx.DiGraph) -> List[int]:
        return [v for v, d in dag.in_degree() if d == 0]

    @staticmethod
    def get_sink_nodes(dag: nx.DiGraph) -> List[int]:
        return [v for v, d in dag.out_degree() if d == 0]

    @staticmethod
    def regular_nodes(dag: nx.DiGraph) -> List[int]:
        return [n for n in dag.nodes()
                if dag.nodes[n].get("node_type", "regular") == "regular"]

    @staticmethod
    def get_option_min(option: Optional[Union[list, int, float]]) -> Optional[Union[int, float]]:
        if option is None:
            return None
        if isinstance(option, list):
            return min(option)
        else:
            return option

    @staticmethod
    def get_option_max(option: Optional[Union[list, int, float]]) -> Optional[Union[int, float]]:
        if option is None:
            return None
        if isinstance(option, list):
            return max(option)
        else:
            return option

    @staticmethod
    def get_critical_path_length(dag: nx.DiGraph, source: int, exit: int) -> int:
        """Get critical path length from 'source' to 'exit'.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG. Every node reachable from 'source' up to and including
            'exit' must already have 'execution_time' set.
        source : int
            Index of path source.
        exit : int
            Index of path exit.

        Returns
        -------
        int
            Critical path length. 0 if 'exit' is not reachable from 'source'.

        Notes
        -----
        If the edge has 'Communication time',
        'Communication time' is also included in critical path length.

        Computed with a topological-order dynamic program (O(V+E)) rather
        than enumerating all simple paths (nx.all_simple_paths), whose
        count can be exponential in the size of the DAG, especially once
        branching constructs are present.

        """
        longest_from_source = {source: dag.nodes[source]["execution_time"]}
        for node in nx.topological_sort(dag):
            if node not in longest_from_source or node == exit:
                continue
            for succ in dag.successors(node):
                edge_len = dag.nodes[succ]["execution_time"]
                if dag.edges[node, succ].get("communication_time"):
                    edge_len += dag.edges[node, succ]["communication_time"]
                candidate = longest_from_source[node] + edge_len
                if candidate > longest_from_source.get(succ, 0):
                    longest_from_source[succ] = candidate

        return longest_from_source.get(exit, 0)

    @staticmethod
    def get_min_in_node(dag: nx.DiGraph, option: Collection[int]) -> int:
        min_in_node_i: int
        min_in = sys.maxsize
        for node_i in option:
            if (in_degree := dag.in_degree(node_i)) < min_in:
                min_in_node_i = node_i
                min_in = in_degree
            if min_in == 0:
                break

        return min_in_node_i

    @staticmethod
    def get_min_out_node(dag: nx.DiGraph, option: Collection[int]) -> int:
        min_out_node_i: int
        min_out = sys.maxsize
        for node_i in option:
            if (out_degree := dag.out_degree(node_i)) < min_out:
                min_out_node_i = node_i
                min_out = out_degree
            if min_out == 0:
                break

        return min_out_node_i
