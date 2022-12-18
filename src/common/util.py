import random
import sys
from typing import Any, Collection, List, Union

import networkx as nx


class Util:
    """Utilization class."""

    @staticmethod
    def ambiguous_equals(s: str, comparison: str) -> bool:
        return s.lower().replace(" ", "") == comparison.lower().replace(" ", "")

    @staticmethod
    def convert_to_property(param_name: str) -> str:
        return param_name.lower().replace(" ", "_")

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
    def get_entry_nodes(dag: nx.DiGraph) -> List[int]:
        return [v for v, d in dag.in_degree() if d == 0]

    @staticmethod
    def get_exit_nodes(dag: nx.DiGraph) -> List[int]:
        return [v for v, d in dag.out_degree() if d == 0]

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
