import random

import networkx as nx
import pytest

from src.common import Util
from src.config import Config
from src.dag_builder import DAGBuilderFactory
from src.exceptions import BuildFailedError, InfeasibleConfigError


def get_config(
    number_of_nodes: int, in_degree: int, out_degree: int, number_of_source_nodes: int
) -> Config:
    config_raw = {
        "Seed": 0,
        "Number of DAGs": 100,
        "Graph structure": {
            "Generation method": "Fan-in/Fan-out",
            "Number of nodes": number_of_nodes,
            "In-degree": in_degree,
            "Out-degree": out_degree,
            "Number of source nodes": number_of_source_nodes,
        },
        "Properties": {
            "End-to-end deadline": {"Ratio of deadline to critical path": {"Random": [1.0, 1.1]}}
        },
        "Output formats": {"DAG": {"YAML": True}},
    }
    return Config(config_raw)


class TestFanInFanOutBuilder:
    def test_validate_config(self):
        config_raw = get_config(1, 1, 1, 2)
        with pytest.raises(InfeasibleConfigError) as e:
            DAGBuilderFactory.create_instance(config_raw)

        assert ">" in str(e.value)

    @pytest.mark.parametrize("number_of_nodes", list(range(10, 200)))
    def test_build_number_of_nodes_upper_10(
        self,
        number_of_nodes,
    ):
        in_degree = random.randint(1, 5)
        out_degree = random.randint(1, 5)
        number_of_source_nodes = random.randint(1, 5)
        try:
            fan_in_fan_out = DAGBuilderFactory.create_instance(
                get_config(number_of_nodes, in_degree, out_degree, number_of_source_nodes)
            )
        except InfeasibleConfigError:
            return 0

        dag_iter = fan_in_fan_out.build()
        try:
            for dag in dag_iter:
                assert nx.is_directed_acyclic_graph(dag)
                for node_i in dag.nodes():
                    assert dag.in_degree(node_i) <= in_degree
                    assert dag.out_degree(node_i) <= out_degree
                assert dag.number_of_nodes() == number_of_nodes
                assert len(Util.get_source_nodes(dag)) == number_of_source_nodes
        except BuildFailedError:
            return 0

    @pytest.mark.parametrize("number_of_nodes", list(range(1, 10)))
    def test_build_number_of_nodes_lower_10(self, number_of_nodes):
        in_degree = random.randint(1, 5)
        out_degree = random.randint(1, 5)
        number_of_source_nodes = random.randint(1, 5)
        try:
            fan_in_fan_out = DAGBuilderFactory.create_instance(
                get_config(
                    number_of_nodes,
                    in_degree,
                    out_degree,
                    number_of_source_nodes,
                )
            )
        except InfeasibleConfigError:
            return 0

        dag_iter = fan_in_fan_out.build()
        try:
            for dag in dag_iter:
                assert nx.is_directed_acyclic_graph(dag)
                for node_i in dag.nodes():
                    assert dag.in_degree(node_i) <= in_degree
                    assert dag.out_degree(node_i) <= out_degree
                assert dag.number_of_nodes() == number_of_nodes
                assert len(Util.get_source_nodes(dag)) == number_of_source_nodes
        except BuildFailedError:
            return 0

    @pytest.mark.parametrize("number_of_exit_nodes", list(range(1, 6)))
    def test_exist_number_of_exit_nodes(self, number_of_exit_nodes):
        number_of_nodes = random.randint(10, 20)
        in_degree = random.randint(1, 5)
        out_degree = random.randint(1, 5)
        number_of_source_nodes = random.randint(1, 5)
        config_raw = {
            "Seed": 0,
            "Number of DAGs": 100,
            "Graph structure": {
                "Generation method": "Fan-in/Fan-out",
                "Number of nodes": number_of_nodes,
                "In-degree": in_degree,
                "Out-degree": out_degree,
                "Number of source nodes": number_of_source_nodes,
                "Number of sink nodes": number_of_exit_nodes,
            },
            "Properties": {
                "End-to-end deadline": {
                    "Ratio of deadline to critical path": {"Random": [1.0, 1.1]}
                }
            },
            "Output formats": {"DAG": {"YAML": True}},
        }

        try:
            fan_in_fan_out = DAGBuilderFactory.create_instance(Config(config_raw))
        except InfeasibleConfigError:
            return 0

        dag_iter = fan_in_fan_out.build()
        try:
            for dag in dag_iter:
                assert nx.is_directed_acyclic_graph(dag)
                for node_i in dag.nodes() - Util.get_exit_nodes(dag):
                    assert dag.in_degree(node_i) <= in_degree
                assert dag.number_of_nodes() == number_of_nodes
                assert len(Util.get_source_nodes(dag)) == number_of_source_nodes
        except BuildFailedError:
            return 0
