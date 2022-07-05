import networkx as nx
import pytest
from src.exceptions import InvalidArgumentError
from src.property_setter.EPU_setter import EPUSetter


@pytest.fixture
def G() -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from([1, 3, 2, 5, 8, 11, 13, 43, 32, 0])

    return G


class TestEPUSetter:

    def test_UUniFast_01(self, G):
        with pytest.raises(InvalidArgumentError) as e:
            EPUSetter._UUniFast(G, 20, 1.0)

        assert str(e.value) == '(total_U/n) >= upper_U'

    def test_UUniFast_02(self, G):
        EPUSetter._UUniFast(G, 10.0)
        sum = 0
        for node_i in G.nodes:
            sum += G.nodes[node_i]['Utilization']
        assert 10.0-0.000001 <= sum <= 10.0+0.000001

    def test_UUniFast_03(self, G):
        EPUSetter._UUniFast(G, 8.0, 1.0)
        sum = 0
        for node_i in G.nodes:
            assert G.nodes[node_i]['Utilization'] <= 1.0
            sum += G.nodes[node_i]['Utilization']
        assert 8.0-0.000001 <= sum <= 8.0+0.000001
