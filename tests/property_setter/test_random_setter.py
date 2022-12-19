import networkx as nx

from src.config import Config
from src.property_setter.random_setter import RandomSetter


class TestRandomSetter:
    def test_set_node(self, mocker):
        param_name = "Execution time"
        exec_option = list(range(10, 100, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "execution_time", exec_option)
        random_setter = RandomSetter(config_mock, param_name, "node")
        dag = nx.DiGraph()
        dag.add_nodes_from(list(range(0, 30)))

        random_setter.set(dag)

        for node_i in dag.nodes:
            assert dag.nodes[node_i][param_name] in exec_option

    def test_set_edge(self, mocker):
        param_name = "Communication time"
        comm_option = list(range(10, 100, 10))

        config_mock = mocker.Mock(spec=Config)
        mocker.patch.object(config_mock, "communication_time", comm_option)
        random_setter = RandomSetter(config_mock, param_name, "edge")
        dag = nx.DiGraph()
        dag.add_nodes_from(list(range(0, 30)))
        dag.add_edges_from([(i, i + 1) for i in range(29)])

        random_setter.set(dag)

        for src_i, tgt_i in dag.edges:
            assert dag.edges[src_i, tgt_i][param_name] in comm_option
