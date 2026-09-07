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


def test_ccr_follows_branching_accounting(mocker):
    import random
    from src.branching_structure import BranchingStructure
    from tests.test_branching_structure import nested_pdag

    random.seed(0)
    config_mock = mocker.Mock(spec=Config)
    mocker.patch.object(config_mock, "ccr", 1.0)
    mocker.patch.object(config_mock, "execution_time", list(range(1000, 10000, 1000)))
    mocker.patch.object(config_mock, "communication_time", None)
    mocker.patch.object(config_mock, "branching_accounting", "max-branch")
    dag, _ = nested_pdag()
    # Insert regular nodes so that regular-to-regular edges exist at every level.
    for before, new, after in ((0, 11, 1), (3, 12, 6), (7, 13, 9)):
        attrs = dict(dag.edges[before, after])
        dag.remove_edge(before, after)
        dag.add_node(new, node_type="regular", execution_time=1)
        dag.add_edge(before, new)
        dag.add_edge(new, after, **attrs)
    CCRSetter(config_mock).set(dag)

    s = BranchingStructure(dag)
    execs = {n: a["execution_time"] for n, a in dag.nodes(data=True)}
    comms = {(u, v): d["communication_time"] for u, v, d in dag.edges(data=True)
             if "communication_time" in d}
    assert set(comms) == {(0, 11), (3, 12), (7, 13)}
    achieved = s.aggregate(comms, "max-branch") / s.aggregate(execs, "max-branch")
    assert abs(achieved - 1.0) <= 0.01


def test_ccr_setter_without_regular_edges_does_not_fail(mocker):
    from tests.test_branching_structure import nested_pdag

    config_mock = mocker.Mock(spec=Config)
    mocker.patch.object(config_mock, "ccr", 1.0)
    mocker.patch.object(config_mock, "execution_time", [10, 20])
    mocker.patch.object(config_mock, "communication_time", None)
    mocker.patch.object(config_mock, "branching_accounting", "all")
    dag, _ = nested_pdag()  # every edge touches a v_ent or v_ext
    CCRSetter(config_mock).set(dag)
    assert not any("communication_time" in d for _, _, d in dag.edges(data=True))
