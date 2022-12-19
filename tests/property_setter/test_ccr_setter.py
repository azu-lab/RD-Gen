from typing import List

import networkx as nx

from src.config import Config
from src.property_setter.ccr_setter import CCRSetter


def create_sequence(dag: nx.DiGraph, nodes: List[int]) -> None:
    dag.add_node(nodes[0])
    for i in nodes[1:]:
        dag.add_edge(i - 1, i)


class TestRandomSetter:
    def test_set_by_exec(self, mocker):
        ccr = 1.0
        exec_option = list(range(10, 100, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "ccr", ccr)
        mocker.patch.object(config_mock, "execution_time", exec_option)
        setter = CCRSetter(config_mock)

        dag = nx.DiGraph()
        create_sequence(dag, list(range(0, 30)))

        setter.set(dag)

        sum_exec = 0
        for node_i in dag.nodes:
            exec = dag.nodes[node_i]["execution_time"]
            assert isinstance(exec, int)
            assert exec >= 1
            sum_exec += exec
        sum_comm = 0
        for src_i, tgt_i in dag.edges:
            comm = dag.edges[src_i, tgt_i]["communication_time"]
            assert isinstance(comm, int)
            assert comm >= 1
            sum_comm += comm

        assert sum_comm / sum_exec - ccr <= 10 ** (-10)

    def test_set_by_comm(self, mocker):
        ccr = 1.0
        comm_option = list(range(10, 100, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "ccr", ccr)
        mocker.patch.object(config_mock, "execution_time", None)
        mocker.patch.object(config_mock, "communication_time", comm_option)
        setter = CCRSetter(config_mock)

        dag = nx.DiGraph()
        create_sequence(dag, list(range(0, 30)))

        setter.set(dag)

        sum_exec = 0
        for node_i in dag.nodes:
            exec = dag.nodes[node_i]["execution_time"]
            assert isinstance(exec, int)
            assert exec >= 1
            sum_exec += exec
        sum_comm = 0
        for src_i, tgt_i in dag.edges:
            comm = dag.edges[src_i, tgt_i]["communication_time"]
            assert isinstance(comm, int)
            assert comm >= 1
            sum_comm += comm

        assert sum_comm / sum_exec - ccr <= 10 ** (-10)

    def test_set_small(self, mocker):
        ccr = 1000.0
        comm_option = 1

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "ccr", ccr)
        mocker.patch.object(config_mock, "execution_time", None)
        mocker.patch.object(config_mock, "communication_time", comm_option)
        setter = CCRSetter(config_mock)

        dag = nx.DiGraph()
        create_sequence(dag, list(range(0, 30)))

        setter.set(dag)

        for node_i in dag.nodes:
            exec = dag.nodes[node_i]["execution_time"]
            assert isinstance(exec, int)
            assert exec == 1
