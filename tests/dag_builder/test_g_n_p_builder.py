import random

import networkx as nx
import numpy as np
import pytest

from src.config import Config
from src.dag_builder import DAGBuilderFactory
from src.exceptions import BuildFailedError, InfeasibleConfigError


def get_config_raw(number_of_nodes: int, probability_of_edge: float) -> dict:
    config_raw = {
        "Seed": 0,
        "Number of DAGs": 100,
        "Graph structure": {
            "Generation method": "G(n, p)",
            "Probability of edge": probability_of_edge,
            "Number of nodes": number_of_nodes,
            "Ensure weakly connected": True,
        },
        "Properties": {
            "End-to-end deadline": {"Ratio of deadline to critical path": {"Random": [1.0, 1.1]}}
        },
        "Output formats": {"DAG": {"YAML": True}},
    }
    return config_raw


class TestGNPBuilder:
    def test_validate_config(self):
        config_raw = get_config_raw(1, 1.0)
        config_raw["Graph structure"]["Number of source nodes"] = 5
        with pytest.raises(InfeasibleConfigError) as e:
            DAGBuilderFactory.create_instance(Config(config_raw))

        assert ">" in str(e.value)

    @pytest.mark.parametrize("probability_of_edge", np.arange(0, 1.0, 0.01).tolist())
    def test_build_normal(self, probability_of_edge):
        number_of_nodes = random.randint(1, 100)
        config_raw = get_config_raw(number_of_nodes, probability_of_edge)
        try:
            gnp = DAGBuilderFactory.create_instance(Config(config_raw))
        except InfeasibleConfigError:
            return 0

        dag_iter = gnp.build()
        try:
            for dag in dag_iter:
                assert nx.is_directed_acyclic_graph(dag)
                assert dag.number_of_nodes() == number_of_nodes
        except BuildFailedError:
            return 0

    def test_build_prob_upper_1(self):
        prob = 1.1
        config_raw = get_config_raw(10, prob)
        gnp = DAGBuilderFactory.create_instance(Config(config_raw))

        dag_iter = gnp.build()
        try:
            for dag in dag_iter:
                assert nx.is_directed_acyclic_graph(dag)
        except BuildFailedError:
            return 0
