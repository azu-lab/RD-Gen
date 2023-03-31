import random
from typing import List

import networkx as nx
import pytest

from src.config import Config
from src.dag_builder.chain_based_builder import Chain, ChainBasedDAG
from src.property_setter.utilization_setter import UtilizationSetter


def get_chains(
    number_of_chains: int, main_sequence_length: int, number_of_sub_sequence: int
) -> List[Chain]:
    chains: List[Chain] = []
    start_idx = 0
    for _ in range(number_of_chains):
        chain = Chain(start_idx)
        chain.build_chain(main_sequence_length, number_of_sub_sequence)
        chains.append(chain)
        start_idx = chain.end_idx + 1

    return chains


class TestUtilizationSetter:
    def test_set_by_only_max_utilization_normal(self, mocker):
        max_utilization = 1.0
        period_option = list(range(10, 100, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "maximum_utilization", max_utilization)
        mocker.patch.object(config_mock, "period", period_option)
        mocker.patch.object(config_mock, "source_node_period", None)
        mocker.patch.object(config_mock, "sink_node_period", None)
        mocker.patch.object(config_mock, "periodic_type", "All")
        util_setter = UtilizationSetter(config_mock)
        dag = nx.DiGraph()
        dag.add_nodes_from(list(range(0, 30)))

        util_setter._set_by_only_max_utilization(dag)

        for node_i in dag.nodes():
            assert dag.nodes[node_i]["period"] in period_option
            assert dag.nodes[node_i]["execution_time"] >= 1
            assert (
                dag.nodes[node_i]["execution_time"] / dag.nodes[node_i]["period"]
                <= max_utilization
            )

    def test_set_by_only_max_utilization_small_period(self, mocker):
        max_utilization = 1.0
        period_option = 1

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "maximum_utilization", max_utilization)
        mocker.patch.object(config_mock, "period", period_option)
        mocker.patch.object(config_mock, "source_node_period", None)
        mocker.patch.object(config_mock, "sink_node_period", None)
        mocker.patch.object(config_mock, "periodic_type", "All")
        util_setter = UtilizationSetter(config_mock)
        dag = nx.DiGraph()
        dag.add_nodes_from(list(range(0, 30)))

        util_setter._set_by_only_max_utilization(dag)

        for node_i in dag.nodes():
            assert dag.nodes[node_i]["period"] == 1
            assert dag.nodes[node_i]["execution_time"] >= 1

    def test_set_by_only_max_utilization_chain(self, mocker):
        max_utilization = 1.0
        period_option = list(range(100, 1000, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "maximum_utilization", max_utilization)
        mocker.patch.object(config_mock, "period", period_option)
        mocker.patch.object(config_mock, "source_node_period", None)
        mocker.patch.object(config_mock, "sink_node_period", None)
        mocker.patch.object(config_mock, "periodic_type", "Chain")
        util_setter = UtilizationSetter(config_mock)

        number_of_chains = 5
        chains = get_chains(number_of_chains, 5, 3)
        chain_based_dag = ChainBasedDAG(chains)

        util_setter._set_by_only_max_utilization_chain(chain_based_dag)

        for chain in chain_based_dag.chains:
            sum_exec = 0
            for node_i in chain.nodes:
                if node_i == chain.head:
                    chain_period = chain_based_dag.nodes[node_i]["period"]
                    assert chain_period in period_option
                exec = chain_based_dag.nodes[node_i]["execution_time"]
                assert exec >= 1
                sum_exec += exec
            assert sum_exec / chain_period <= max_utilization

    @pytest.mark.parametrize("n", list(range(1, 30)))
    def test_UUniFast(self, n):
        total_utilization = random.uniform(0.1, n)
        utilizations = UtilizationSetter._UUniFast(total_utilization, n)

        assert len(utilizations) == n
        sum_util = 0
        for util in utilizations:
            sum_util += util
        assert abs(sum_util - total_utilization) <= 0.000001

    @pytest.mark.parametrize("n", list(range(1, 30)))
    def test_UUniFast_with_max_u(self, n):
        total_utilization = random.uniform(0.1, n)
        max_utilization = 1.0
        utilizations = UtilizationSetter._UUniFast_with_max_u(
            total_utilization, n, max_utilization
        )

        assert len(utilizations) == n
        sum_util = 0
        for util in utilizations:
            assert util <= max_utilization
            sum_util += util
        assert abs(sum_util - total_utilization) <= 0.000001

    def test_set_by_total_utilization_no_max(self, mocker):
        total_utilization = 10.0
        period_option = list(range(1000, 10000, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "total_utilization", total_utilization)
        mocker.patch.object(config_mock, "maximum_utilization", None)
        mocker.patch.object(config_mock, "period", period_option)
        mocker.patch.object(config_mock, "source_node_period", None)
        mocker.patch.object(config_mock, "sink_node_period", None)
        mocker.patch.object(config_mock, "periodic_type", "All")
        util_setter = UtilizationSetter(config_mock)
        dag = nx.DiGraph()
        dag.add_nodes_from(list(range(0, 30)))

        util_setter._set_by_total_utilization(dag)

        after_total_util = 0
        for node_i in dag.nodes():
            assert dag.nodes[node_i]["period"] in period_option
            assert dag.nodes[node_i]["execution_time"] >= 1
            after_total_util += dag.nodes[node_i]["execution_time"] / dag.nodes[node_i]["period"]

        assert abs(after_total_util - total_utilization) <= 0.01

    def test_set_by_total_utilization_with_max_ok(self, mocker):
        max_utilization = 1.0
        total_utilization = 10.0
        period_option = list(range(1000, 10000, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "total_utilization", total_utilization)
        mocker.patch.object(config_mock, "maximum_utilization", max_utilization)
        mocker.patch.object(config_mock, "period", period_option)
        mocker.patch.object(config_mock, "source_node_period", None)
        mocker.patch.object(config_mock, "sink_node_period", None)
        mocker.patch.object(config_mock, "periodic_type", "All")
        util_setter = UtilizationSetter(config_mock)
        dag = nx.DiGraph()
        dag.add_nodes_from(list(range(0, 30)))

        util_setter._set_by_total_utilization(dag)

        after_total_util = 0
        for node_i in dag.nodes():
            assert dag.nodes[node_i]["period"] in period_option
            assert dag.nodes[node_i]["execution_time"] >= 1
            util = dag.nodes[node_i]["execution_time"] / dag.nodes[node_i]["period"]
            assert util <= max_utilization
            after_total_util += util

        assert abs(after_total_util - total_utilization) <= 0.01

    def test_set_by_total_utilization_with_max_infeasible(self, mocker):
        max_utilization = 1.0
        total_utilization = 100.0
        number_of_nodes = 10
        period_option = list(range(1000, 10000, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "total_utilization", total_utilization)
        mocker.patch.object(config_mock, "maximum_utilization", max_utilization)
        mocker.patch.object(config_mock, "period", period_option)
        mocker.patch.object(config_mock, "source_node_period", None)
        mocker.patch.object(config_mock, "sink_node_period", None)
        mocker.patch.object(config_mock, "periodic_type", "All")
        util_setter = UtilizationSetter(config_mock)
        dag = nx.DiGraph()
        dag.add_nodes_from(list(range(0, number_of_nodes)))

        util_setter._set_by_total_utilization(dag)

        for node_i in dag.nodes():
            assert dag.nodes[node_i]["period"] in period_option
            assert dag.nodes[node_i]["execution_time"] >= 1
            util = dag.nodes[node_i]["execution_time"] / dag.nodes[node_i]["period"]
            assert abs(util - max_utilization) <= 0.001

    def test_set_by_total_utilization_chain(self, mocker):
        max_utilization = 1.0
        total_utilization = 3.0
        period_option = list(range(10000, 100000, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "total_utilization", total_utilization)
        mocker.patch.object(config_mock, "maximum_utilization", max_utilization)
        mocker.patch.object(config_mock, "period", period_option)
        mocker.patch.object(config_mock, "source_node_period", None)
        mocker.patch.object(config_mock, "sink_node_period", None)
        mocker.patch.object(config_mock, "periodic_type", "Chain")
        util_setter = UtilizationSetter(config_mock)

        number_of_chains = 5
        chains = get_chains(number_of_chains, 5, 3)
        chain_based_dag = ChainBasedDAG(chains)

        util_setter._set_by_total_utilization_chain(chain_based_dag)

        after_total_utilization = 0
        for chain in chain_based_dag.chains:
            sum_exec = 0
            for node_i in chain.nodes:
                if node_i == chain.head:
                    chain_period = chain_based_dag.nodes[node_i]["period"]
                    assert chain_period in period_option
                exec = chain_based_dag.nodes[node_i]["execution_time"]
                assert exec >= 1
                sum_exec += exec
            chain_utilization = sum_exec / chain_period
            assert chain_utilization <= max_utilization
            after_total_utilization += chain_utilization

        assert abs(after_total_utilization - total_utilization) <= 0.01
