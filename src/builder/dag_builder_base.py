import random
import sys
from abc import ABCMeta, abstractmethod
from typing import Generator, List, Tuple, Union

import networkx as nx
from src.config import Config
from src.exceptions import InvalidArgumentError


class DAGBuilderBase(metaclass=ABCMeta):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        self._cfg = cfg

    @abstractmethod
    def build(self) -> Generator[nx.DiGraph, None, None]:
        raise NotImplementedError

    def _add_min_edges(  # HACK
        self,
        src_layer: List[int],
        tgt_layer: List[int],
        G: nx.DiGraph
    ) -> None:
        def is_finish() -> bool:
            [v for v, d in G.out_degree() if d == 0]
            for src_node_i in src_layer:
                if G.out_degree(src_node_i) == 0:
                    return False
            for tgt_node_i in tgt_layer:
                if G.in_degree(tgt_node_i) == 0:
                    return False

            return True

        while not is_finish():
            # Search min_out_src
            min_out_src = src_layer[0]
            min_out = G.out_degree(src_layer[0])
            for src_node_i in src_layer[1:]:
                if min_out == 0:
                    break
                if G.out_degree(src_node_i) < min_out:
                    min_out_src = src_node_i
                    min_out = G.out_degree(src_node_i)

            # Search min_in_tgt
            min_in_tgt = tgt_layer[0]
            min_in = G.in_degree(tgt_layer[0])
            for tgt_node_i in tgt_layer[1:]:
                if min_in == 0:
                    break
                if G.in_degree(tgt_node_i) < min_in:
                    min_in_tgt = tgt_node_i
                    min_in = G.in_degree(tgt_node_i)

            # Add edge
            G.add_edge(min_out_src, min_in_tgt)

    def random_choice(
        self,
        param_value: Union[int, float, List]
    ) -> Union[int, float]:
        if not param_value:
            raise InvalidArgumentError

        if isinstance(param_value, list):
            choose_value = random.choice(param_value)
        else:
            choose_value = param_value

        return choose_value

    def get_bound(
        self,
        max_or_min: str,
        param_value: Union[int, float, List]
    ) -> Union[int, float]:
        if not param_value:
            raise InvalidArgumentError

        if isinstance(param_value, list):
            if max_or_min == "max":
                bound = max(param_value)
            elif max_or_min == "min":
                bound = min(param_value)
            else:
                raise InvalidArgumentError()
        else:
            bound = param_value

        return bound

    def get_random_bool(
        self
    ) -> bool:
        random_int = random.randint(1, 10)
        if random_int <= 5:
            return True
        else:
            return False

    def ensure_weakly_connected(
        self,
        G: nx.DiGraph
    ) -> None:
        if len(comps := list(nx.weakly_connected_components(G))) >= 2:
            comps.sort(key=lambda x: len(x))
            tgt_comp = comps.pop(-1)
            tgt_nodes = tgt_comp - {v for v, d in G.in_degree() if d == 0}
            exit_nodes = {v for v, d in G.out_degree() if d == 0}
            for comp in comps:
                comp_exits = set(comp) & exit_nodes
                src_i = random.choice(list(comp_exits))
                tgt_in_degree = {G.in_degree(t): t for t in tgt_nodes}
                G.add_edge(src_i, min(tgt_in_degree.items())[1])
