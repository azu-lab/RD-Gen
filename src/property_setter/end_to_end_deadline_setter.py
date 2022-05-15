from typing import Dict, List, Tuple, Union

import networkx as nx
from src.input_parameter import InputParameter
from src.property_setter.property_setter_base import PropertySetterBase


class E2EDeadlineSetter(PropertySetterBase):
    def __init__(
        self,
        base_param: InputParameter
    ) -> None:
        self._choices = base_param.get_child_value(
            "ratio of deadline to critical path")

    def _get_cp(
        self,
        dag: nx.DiGraph,
        source,
        exit
    ) -> Tuple[List[int], int]:
        cp = []
        cp_len = 0

        paths = nx.all_simple_paths(dag, source=source, target=exit)
        for path in paths:
            path_len = 0
            for i in range(len(path)):
                path_len += dag.nodes[path[i]]['Execution time']
                if(i != len(path)-1 and
                        'Communication time'
                        in list(dag.edges[path[i], path[i+1]].keys())):
                    path_len += dag.edges[path[i],
                                          path[i+1]]['Communication time']
            if(path_len > cp_len):
                cp = path
                cp_len = path_len

        return cp, cp_len

    def set(
        self,
        G: nx.DiGraph
    ) -> None:
        for exit_i in [v for v, d in G.out_degree() if d == 0]:
            max_cp_len = 0
            for entry_i in [v for v, d in G.in_degree() if d == 0]:
                _, cp_len = self._get_cp(G, entry_i, exit_i)
                if(cp_len > max_cp_len):
                    max_cp_len = cp_len
            G.nodes[exit_i]['End-to-end deadline'] = \
                int(max_cp_len * self.choice_one(self._choices))
