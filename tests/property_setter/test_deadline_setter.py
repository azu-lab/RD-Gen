from typing import List

import networkx as nx
import pytest

from src.config import Config
from src.exceptions import BuildFailedError
from src.property_setter.deadline_setter import DeadlineSetter


def create_sequence(dag: nx.DiGraph, nodes: List[int]) -> None:
    dag.add_node(nodes[0])
    for i in nodes[1:]:
        dag.add_edge(i - 1, i)


def create_fan_in_dag() -> nx.DiGraph:
    """Create entry(0) -> {1,2 -> ... , 3,4,5 -> ...} -> exit(6), cp length 5."""
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
    return dag


class TestRandomSetter:
    def test_get_cp_len_only_exec(self):
        dag = create_fan_in_dag()

        cp_len = DeadlineSetter._get_cp_len(dag, 0, 6)
        assert cp_len == 5

    def test_get_cp_len_with_communication_time(self):
        dag = create_fan_in_dag()
        # Path 0->1->2->6 has 4 nodes (len 4); adding a large communication
        # time on (0, 1) makes it the critical path over 0->3->4->5->6 (len 5).
        dag.edges[0, 1]["communication_time"] = 10

        cp_len = DeadlineSetter._get_cp_len(dag, 0, 6)
        assert cp_len == 14

    def test_get_cp_len_unreachable(self):
        dag = create_fan_in_dag()
        dag.add_node(99, execution_time=1)

        cp_len = DeadlineSetter._get_cp_len(dag, 99, 6)
        assert cp_len == 0

    def test_set_arbitrary(self, mocker):
        ratio = 1.1

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "deadline_mode", "Arbitrary")
        mocker.patch.object(config_mock, "ratio_of_deadline_to_critical_path", ratio)
        setter = DeadlineSetter(config_mock)

        dag = create_fan_in_dag()

        setter.set(dag)
        assert dag.nodes[6]["end_to_end_deadline"] == int(5 * ratio)

    def test_set_implicit(self, mocker):
        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "deadline_mode", "Implicit")
        setter = DeadlineSetter(config_mock)

        dag = create_fan_in_dag()
        dag.nodes[0]["period"] = 100

        setter.set(dag)
        assert dag.nodes[6]["end_to_end_deadline"] == 100

    def test_set_implicit_boundary_equal_is_feasible(self, mocker):
        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "deadline_mode", "Implicit")
        setter = DeadlineSetter(config_mock)

        dag = create_fan_in_dag()
        dag.nodes[0]["period"] = 5  # equal to critical path length -> still feasible (L == D)

        setter.set(dag)
        assert dag.nodes[6]["end_to_end_deadline"] == 5

    def test_set_implicit_infeasible_raises(self, mocker):
        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "deadline_mode", "Implicit")
        setter = DeadlineSetter(config_mock)

        dag = create_fan_in_dag()
        dag.nodes[0]["period"] = 4  # less than critical path length (5) -> infeasible

        with pytest.raises(BuildFailedError):
            setter.set(dag)

    def test_set_constrained(self, mocker):
        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "deadline_mode", "Constrained")
        setter = DeadlineSetter(config_mock)

        dag = create_fan_in_dag()
        dag.nodes[0]["period"] = 100

        setter.set(dag)
        deadline = dag.nodes[6]["end_to_end_deadline"]
        assert 5 < deadline <= 100

    def test_set_constrained_infeasible_raises(self, mocker):
        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "deadline_mode", "Constrained")
        setter = DeadlineSetter(config_mock)

        dag = create_fan_in_dag()
        dag.nodes[0]["period"] = 5  # equal to critical path length -> infeasible

        with pytest.raises(BuildFailedError):
            setter.set(dag)

    def test_set_heterogeneous_periods_raises(self, mocker):
        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "deadline_mode", "Implicit")
        setter = DeadlineSetter(config_mock)

        dag = create_fan_in_dag()
        # Two source nodes reaching the same sink with different periods.
        dag.add_node(7, execution_time=1)
        dag.add_edge(7, 5)
        dag.nodes[0]["period"] = 100
        dag.nodes[7]["period"] = 200

        with pytest.raises(BuildFailedError):
            setter.set(dag)
