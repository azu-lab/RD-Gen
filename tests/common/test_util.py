import networkx as nx

from src.common import Util


class TestUtil:
    def test_ambiguous_equals_s_upper(self):
        assert Util.ambiguous_equals("APPLE", "apple")

    def test_ambiguous_equals_space(self):
        assert Util.ambiguous_equals("ap ple", "apple")

    def test_random_choice_list(self):
        assert Util.random_choice([1, 2]) in [1, 2]

    def test_random_choice_not_list(self):
        assert Util.random_choice(1) == 1

    def test_get_min_in_node_exist_0(self):
        G = nx.DiGraph()
        G.add_node(0)
        G.add_edge(0, 1)
        assert Util.get_min_in_node(G, [0, 1]) == 0

    def test_get_min_in_node_normal(self):
        G = nx.DiGraph()
        G.add_nodes_from([0, 1])
        G.add_nodes_from([2, 3, 4])
        G.add_edges_from([(0, 2), (0, 3), (0, 4)])
        G.add_edges_from([(1, 2), (1, 3)])

        assert Util.get_min_in_node(G, [2, 3, 4]) == 4

    def test_get_min_out_node_exist_0(self):
        G = nx.DiGraph()
        G.add_nodes_from([0, 1, 2])
        G.add_edges_from([(0, 1), (1, 0)])

        assert Util.get_min_out_node(G, [0, 1, 2]) == 2

    def test_get_min_out_node_normal(self):
        G = nx.DiGraph()
        G.add_nodes_from([0, 1, 2])
        G.add_nodes_from([3, 4])
        G.add_edges_from([(0, 3), (0, 4), (1, 3), (1, 4), (2, 3)])

        assert Util.get_min_out_node(G, [0, 1, 2]) == 2
