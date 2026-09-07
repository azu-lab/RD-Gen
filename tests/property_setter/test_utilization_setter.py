import random
from typing import List

import networkx as nx
import pytest

from src.common import Util
from src.config import Config
from src.dag_builder.chain_based_builder import Chain, ChainBasedDAG
from src.property_setter.utilization_setter import UtilizationSetter
from src.branching_structure import BranchingStructure
from src.dag_builder.branching_augmentor import BranchingAugmentor
from tests.test_branching_structure import nested_pdag


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


def _dag_type_mock(mocker, accounting, total_utilization=0.5, max_utilization=None):
    config_mock = mocker.Mock(spec=Config)
    mocker.patch.object(config_mock, "total_utilization", total_utilization)
    mocker.patch.object(config_mock, "maximum_utilization", max_utilization)
    mocker.patch.object(config_mock, "period", 100000)
    mocker.patch.object(config_mock, "source_node_period", None)
    mocker.patch.object(config_mock, "sink_node_period", None)
    mocker.patch.object(config_mock, "periodic_type", "DAG")
    mocker.patch.object(config_mock, "execution_time", None)
    mocker.patch.object(config_mock, "branching_accounting", accounting)
    return config_mock


class TestPeriodicTypeDAG:
    @pytest.mark.parametrize("accounting", ["all", "expected", "max-branch"])
    def test_total_utilization_hits_accounted_aggregate(self, mocker, accounting):
        random.seed(0)
        dag, _ = nested_pdag()
        UtilizationSetter(_dag_type_mock(mocker, accounting)).set(dag)

        assert dag.graph["period"] == 100000
        assert dag.nodes[0]["period"] == 100000
        assert all("period" not in dag.nodes[n] for n in dag.nodes() if n != 0)
        for n, a in dag.nodes(data=True):
            if a["node_type"] == "regular":
                assert a["execution_time"] >= 1
            else:
                assert a["execution_time"] == 0
        execs = {n: a["execution_time"] for n, a in dag.nodes(data=True)}
        achieved = BranchingStructure(dag).aggregate(execs, accounting) / 100000
        assert abs(achieved - 0.5) <= 0.001

    def test_only_max_utilization(self, mocker):
        random.seed(0)
        dag, _ = nested_pdag()
        UtilizationSetter(_dag_type_mock(mocker, "max-branch", total_utilization=None,
                                         max_utilization=0.8)).set(dag)
        execs = {n: a["execution_time"] for n, a in dag.nodes(data=True)}
        achieved = BranchingStructure(dag).aggregate(execs, "max-branch") / 100000
        assert 0 < achieved <= 0.8 + 0.001

    def test_accounting_modes_differ_on_the_same_structure(self, mocker):
        random.seed(0)
        dag, _ = nested_pdag()
        UtilizationSetter(_dag_type_mock(mocker, "max-branch")).set(dag)
        execs = {n: a["execution_time"] for n, a in dag.nodes(data=True)}
        s = BranchingStructure(dag)
        assert s.aggregate(execs, "all") > s.aggregate(execs, "max-branch") > s.aggregate(execs, "expected")


class TestPeriodicTypeChainWithBranching:
    def test_chain_utilization_with_branching_constructs(self, mocker):
        random.seed(0)
        raw = {
            "Seed": 0, "Number of DAGs": 1,
            "Graph structure": {
                "Generation method": "Chain-based",
                "Number of chains": 3, "Main sequence length": 5, "Number of sub sequences": 1,
                "Branching": {"Probability of branching": 1.0, "Maximum nesting depth": 1,
                              "Maximum branches": 3, "Firing": "probabilistic",
                              "Probability distribution": "uniform-normalize",
                              "Sub-chain length": 2, "Accounting": "max-branch"},
            },
            "Properties": {}, "Output formats": {"DAG": {"YAML": True}},
        }
        chain_dag = nx.DiGraph(ChainBasedDAG(get_chains(3, 5, 1)))
        dag = BranchingAugmentor(Config(raw)).augment(chain_dag, "chain")
        assert any(a["node_type"] == "v_ent" for _, a in dag.nodes(data=True))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "total_utilization", 1.5)
        mocker.patch.object(config_mock, "maximum_utilization", 1.0)
        mocker.patch.object(config_mock, "period", 1000000)
        mocker.patch.object(config_mock, "source_node_period", None)
        mocker.patch.object(config_mock, "sink_node_period", None)
        mocker.patch.object(config_mock, "periodic_type", "Chain")
        mocker.patch.object(config_mock, "execution_time", None)
        mocker.patch.object(config_mock, "branching_accounting", "max-branch")
        UtilizationSetter(config_mock).set(dag)

        s = BranchingStructure(dag)
        total = 0.0
        for chain_nodes in Util.chains(dag).values():
            head = Util.chain_head(dag, chain_nodes)
            assert dag.nodes[head]["period"] == 1000000
            execs = {n: dag.nodes[n]["execution_time"] for n in chain_nodes}
            total += s.aggregate(execs, "max-branch") / 1000000
        assert abs(total - 1.5) <= 0.001
        timer_nodes = [n for n, a in dag.nodes(data=True) if "period" in a]
        assert sorted(timer_nodes) == sorted(
            Util.chain_head(dag, c) for c in Util.chains(dag).values())
