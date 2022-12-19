from typing import List

import networkx as nx

from src.config import Config
from src.property_setter.deadline_setter import DeadlineSetter


def create_sequence(dag: nx.DiGraph, nodes: List[int]) -> None:
    dag.add_node(nodes[0])
    for i in nodes[1:]:
        dag.add_edge(i - 1, i)


class TestRandomSetter:
    def test_get_cp_len_only_exec(self):
        dag = nx.DiGraph()
        create_sequence(dag, [1, 2])
        dag.nodes[1]["execution_time"] = 1
        dag.nodes[2]["execution_time"] = 1
        create_sequence(dag, [3, 4, 5])
        dag.nodes[3]["execution_time"] = 1
        dag.nodes[4]["execution_time"] = 1
        dag.nodes[5]["execution_time"] = 1

        entry_i = 0
        dag.add_node(entry_i, execution_time=1)
        dag.add_edges_from([(entry_i, 1), (entry_i, 3)])
        exit_i = 6
        dag.add_node(exit_i, execution_time=1)
        dag.add_edges_from([(2, exit_i), (5, exit_i)])

        cp_len = DeadlineSetter._get_cp_len(dag, entry_i, exit_i)
        assert cp_len == 5

    def test_set(self, mocker):
        ratio = 1.1

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "ratio_of_deadline_to_critical_path", ratio)
        setter = DeadlineSetter(config_mock)

        dag = nx.DiGraph()
        create_sequence(dag, [1, 2])
        dag.nodes[1]["execution_time"] = 1
        dag.nodes[2]["execution_time"] = 1
        create_sequence(dag, [3, 4, 5])
        dag.nodes[3]["execution_time"] = 1
        dag.nodes[4]["execution_time"] = 1
        dag.nodes[5]["execution_time"] = 1

        entry_i = 0
        dag.add_node(entry_i, execution_time=1)
        dag.add_edges_from([(entry_i, 1), (entry_i, 3)])
        exit_i = 6
        dag.add_node(exit_i, execution_time=1)
        dag.add_edges_from([(2, exit_i), (5, exit_i)])

        setter.set(dag)
        assert dag.nodes[exit_i]["end_to_end_deadline"] == int(5 * ratio)
