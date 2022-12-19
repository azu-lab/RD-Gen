import networkx as nx

from src.config import Config
from src.property_setter.additional_setter import AdditionalSetter


class TestAdditionalSetter:
    def test_set_node(self, mocker):
        param_name = "Node new"
        option = list(range(10, 100, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "node_properties", {param_name: option})
        mocker.patch.object(config_mock, "edge_properties", None)
        setter = AdditionalSetter(config_mock)
        dag = nx.DiGraph()
        dag.add_nodes_from(list(range(0, 30)))

        setter.set(dag)

        for node_i in dag.nodes:
            assert dag.nodes[node_i][param_name] in option

    def test_set_edge(self, mocker):
        param_name = "Edge new"
        option = list(range(10, 100, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "node_properties", None)
        mocker.patch.object(config_mock, "edge_properties", {param_name: option})
        setter = AdditionalSetter(config_mock)
        dag = nx.DiGraph()
        dag.add_nodes_from(list(range(0, 30)))

        setter.set(dag)

        for src_i, tgt_i in dag.edges:
            dag.edges[src_i, tgt_i][param_name] in option
