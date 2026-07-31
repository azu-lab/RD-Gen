import networkx as nx

from ..common import Util
from ..config import Config
from .property_setter_base import PropertySetterBase


class AdditionalSetter(PropertySetterBase):
    """Additional setter class.

    Set additional parameters completely at random.

    """

    def __init__(self, config: Config) -> None:
        """Constructor.

        Parameters
        ----------
        config : Config
            Config.

        """
        super().__init__(config)

    def _validate_config(self, config: Config) -> None:
        pass

    def set(self, dag: nx.DiGraph) -> None:
        """Completely random set additional properties.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG

        """
        if node_properties := self._config.node_properties:
            for param_name, option in node_properties.items():
                for node_i in Util.regular_nodes(dag):
                    dag.nodes[node_i][param_name] = Util.random_choice(option)

        if edge_properties := self._config.edge_properties:
            for param_name, option in edge_properties.items():
                for src_i, tgt_i in dag.edges:
                    if (dag.nodes[src_i].get("node_type", "regular") == "regular"
                            and dag.nodes[tgt_i].get("node_type", "regular") == "regular"):
                        dag.edges[src_i, tgt_i][param_name] = Util.random_choice(option)
