import random
from typing import List

import networkx as nx
import pytest

from src.common import Util
from src.config.config import Config
from src.dag_builder.chain_based_builder import Chain, ChainBasedDAG
from src.dag_builder.dag_builder_factory import DAGBuilderFactory
from src.exceptions import BuildFailedError


class TestChain:
    @pytest.mark.parametrize("main_sequence_length", list(range(2, 10)))
    def test_build_chain(self, main_sequence_length):
        chain = Chain(0)
        number_of_sub_sequence = random.randint(1, 5)
        chain.build_chain(main_sequence_length, number_of_sub_sequence)

        assert nx.is_directed_acyclic_graph(chain)
        assert len(list(nx.weakly_connected_components(chain))) == 1
        assert chain.main_tail == main_sequence_length - 1
        assert chain.end_idx == chain.number_of_nodes() - 1

        max_len = -1
        for tail_i in Util.get_exit_nodes(chain):
            paths = nx.all_simple_paths(chain, 0, tail_i)
            for path in paths:
                if len(path) > max_len:
                    max_len = len(path)
        assert max_len == main_sequence_length


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


class TestChainBasedDAG:
    @pytest.mark.parametrize("number_of_source_nodes", list(range(1, 11)))
    def test_vertically_link_chains_main_tail(self, number_of_source_nodes):
        number_of_chains = random.randint(number_of_source_nodes, number_of_source_nodes + 10)
        chains = get_chains(number_of_chains, 5, 3)
        chain_based_dag = ChainBasedDAG(chains)

        chain_based_dag.vertically_link_chains(number_of_source_nodes, True, False)

        assert nx.is_directed_acyclic_graph(chain_based_dag)
        assert len(Util.get_source_nodes(chain_based_dag)) == number_of_source_nodes
        all_sub_tails = []
        for chain in chains:
            all_sub_tails += chain.sub_sequence_tails
        for sub_tail_i in all_sub_tails:
            assert chain_based_dag.out_degree(sub_tail_i) == 0

    @pytest.mark.parametrize("number_of_source_nodes", list(range(1, 11)))
    def test_vertically_link_chains_sub_tail(self, number_of_source_nodes):
        number_of_chains = random.randint(number_of_source_nodes, number_of_source_nodes + 10)
        chains = get_chains(number_of_chains, 5, 3)
        chain_based_dag = ChainBasedDAG(chains)

        chain_based_dag.vertically_link_chains(number_of_source_nodes, False, True)

        assert nx.is_directed_acyclic_graph(chain_based_dag)
        assert len(Util.get_source_nodes(chain_based_dag)) == number_of_source_nodes
        all_main_tails = [chain.main_tail for chain in chains]
        for main_tail_i in all_main_tails:
            assert chain_based_dag.out_degree(main_tail_i) == 0

    @pytest.mark.parametrize("number_of_source_nodes", list(range(1, 11)))
    def test_vertically_link_chains_normal(self, number_of_source_nodes):
        number_of_chains = random.randint(number_of_source_nodes, number_of_source_nodes + 10)
        chains = get_chains(number_of_chains, 5, 3)
        chain_based_dag = ChainBasedDAG(chains)

        chain_based_dag.vertically_link_chains(number_of_source_nodes, True, True)

        assert nx.is_directed_acyclic_graph(chain_based_dag)
        assert len(Util.get_source_nodes(chain_based_dag)) == number_of_source_nodes

    @pytest.mark.parametrize("number_of_exit_nodes", list(range(1, 11)))
    def test_merge_chains_middle(self, number_of_exit_nodes):
        number_of_chains = random.randint(number_of_exit_nodes, number_of_exit_nodes + 10)
        chains = get_chains(number_of_chains, 5, 3)
        chain_based_dag = ChainBasedDAG(chains)

        try:
            chain_based_dag.merge_chains(number_of_exit_nodes, True, False)
        except BuildFailedError:
            return 0

        assert nx.is_directed_acyclic_graph(chain_based_dag)
        assert len(Util.get_exit_nodes(chain_based_dag)) == number_of_exit_nodes
        for exit_i in Util.get_exit_nodes(chain_based_dag):
            assert chain_based_dag.in_degree(exit_i) == 1

    @pytest.mark.parametrize("number_of_exit_nodes", list(range(1, 11)))
    def test_merge_chains_exit(self, number_of_exit_nodes):
        number_of_chains = random.randint(number_of_exit_nodes, number_of_exit_nodes + 10)
        chains = get_chains(number_of_chains, 5, 3)
        chain_based_dag = ChainBasedDAG(chains)

        chain_based_dag.merge_chains(number_of_exit_nodes, False, True)

        assert nx.is_directed_acyclic_graph(chain_based_dag)
        assert len(Util.get_exit_nodes(chain_based_dag)) == number_of_exit_nodes
        for middle_i in (
            set(chain_based_dag.nodes())
            - set(Util.get_exit_nodes(chain_based_dag))
            - set(Util.get_source_nodes(chain_based_dag))
        ):
            assert chain_based_dag.in_degree(middle_i) == 1

    @pytest.mark.parametrize("number_of_exit_nodes", list(range(1, 11)))
    def test_merge_chains_normal(self, number_of_exit_nodes):
        number_of_chains = random.randint(number_of_exit_nodes, number_of_exit_nodes + 10)
        chains = get_chains(number_of_chains, 5, 3)
        chain_based_dag = ChainBasedDAG(chains)

        chain_based_dag.merge_chains(number_of_exit_nodes, True, True)

        assert nx.is_directed_acyclic_graph(chain_based_dag)
        assert len(Util.get_exit_nodes(chain_based_dag)) == number_of_exit_nodes


class TestChainBasedBuilder:
    @pytest.mark.parametrize("number_of_chains", list(range(1, 20)))
    def test_build(self, number_of_chains):
        main_sequence_length = random.randint(2, 10)
        number_of_sub_sequence = random.randint(2, 10)
        number_of_source_nodes = random.randint(1, number_of_chains)
        number_of_exit_nodes = random.randint(1, number_of_chains)
        config_raw = {
            "Seed": 0,
            "Number of DAGs": 100,
            "Graph structure": {
                "Generation method": "Chain-based",
                "Number of chains": number_of_chains,
                "Main sequence length": main_sequence_length,
                "Number of sub sequences": number_of_sub_sequence,
                "Vertically link chains": {
                    "Number of source nodes": number_of_source_nodes,
                    "Main sequence tail": True,
                    "Sub sequence tail": True,
                },
                "Merge chains": {
                    "Number of sink nodes": number_of_exit_nodes,
                    "Middle of chain": True,
                    "Sink node": True,
                },
            },
            "Properties": {
                "End-to-end deadline": {
                    "Ratio of deadline to critical path": {"Random": [1.0, 1.1]}
                }
            },
            "Output formats": {"DAG": {"YAML": True}},
        }

        chain_based = DAGBuilderFactory.create_instance(Config(config_raw))

        dag_iter = chain_based.build()
        try:
            for dag in dag_iter:
                assert nx.is_directed_acyclic_graph(dag)
                assert len(Util.get_source_nodes(dag)) == number_of_source_nodes
                assert len(Util.get_exit_nodes(dag)) == number_of_exit_nodes
        except BuildFailedError:
            return 0
