import random

import networkx as nx
import pytest

from src.common import Util
from src.dag_builder.dag_builder_base import DAGBuilderBase


class TestDAGBuilderBase:
    @pytest.mark.parametrize("src_layer_len", list(range(1, 6)))
    @pytest.mark.parametrize("tgt_layer_len", list(range(1, 6)))
    def test_add_minimum_edges(self, src_layer_len, tgt_layer_len):
        G = nx.DiGraph()
        src_layer = []
        for _ in range(src_layer_len):
            node_i = G.number_of_nodes()
            src_layer.append(node_i)
            G.add_node(node_i)
        tgt_layer = []
        for _ in range(tgt_layer_len):
            node_i = G.number_of_nodes()
            tgt_layer.append(node_i)
            G.add_node(node_i)

        DAGBuilderBase._add_minimum_edges(src_layer, tgt_layer, G)
        assert nx.is_directed_acyclic_graph(G)
        for src_i in src_layer:
            assert G.out_degree(src_i) != 0
        for tgt_i in tgt_layer:
            assert G.in_degree(tgt_i) != 0

    @pytest.mark.parametrize("number_of_nodes", list(range(3, 20)))
    def test_ensure_weakly_connected_normal(self, number_of_nodes):
        G = nx.DiGraph()
        nodes = [i for i in range(number_of_nodes)]
        G.add_nodes_from(nodes)
        separate_i = random.choice(nodes[1:-1])
        DAGBuilderBase._add_minimum_edges(nodes[:separate_i], nodes[separate_i:], G)

        before_num_entry = len(Util.get_entry_nodes(G))
        before_num_exit = len(Util.get_exit_nodes(G))
        DAGBuilderBase._ensure_weakly_connected(G)
        assert nx.is_directed_acyclic_graph(G)
        assert len(list(nx.weakly_connected_components(G))) == 1
        assert before_num_entry == len(Util.get_entry_nodes(G))
        assert before_num_exit == len(Util.get_exit_nodes(G))