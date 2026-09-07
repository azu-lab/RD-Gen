import random
import sys
from typing import Any, Collection, Dict, List, Optional, Union

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
    def chains(dag: nx.DiGraph) -> Dict[int, List[int]]:
        """Nodes grouped by ``chain_id`` (empty for non chain-based DAGs)."""
        chains: Dict[int, List[int]] = {}
        for n in sorted(dag.nodes()):
            cid = dag.nodes[n].get("chain_id")
            if cid is not None:
                chains.setdefault(cid, []).append(n)
        return dict(sorted(chains.items()))

    @staticmethod
    def chain_head(dag: nx.DiGraph, chain_nodes: List[int]) -> int:
        """The unique node of a chain with no predecessor inside the chain."""
        members = set(chain_nodes)
        heads = [n for n in chain_nodes
                 if not any(p in members for p in dag.predecessors(n))]
        if len(heads) != 1:
            raise ValueError(f"chain {chain_nodes} has {len(heads)} heads: {heads}")
        return heads[0]

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
