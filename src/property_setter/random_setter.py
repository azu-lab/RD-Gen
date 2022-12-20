import networkx as nx

from ..common import Util
from ..config import Config
from .property_setter_base import PropertySetterBase


class RandomSetter(PropertySetterBase):
    """Random setter class.

    Set the specified parameters completely at random.

    """

    def __init__(self, config: Config, parameter_name: str, target: str) -> None:
        """Constructor.

        Parameters
        ----------
        config : Config
            Config.
        parameter_name : str
            Parameter name.
        target : str
            Target to be set.
            "node" or "edge".

        """
        super().__init__(config)
        self._param_name = parameter_name
        self._target = target

    def _validate_config(self, config: Config) -> None:
        pass

    def set(self, dag: nx.DiGraph) -> None:
        """Completely random set.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG

        """
        property_name = Util.convert_to_property(self._param_name)
        option = getattr(self._config, property_name)
        if self._target == "node":
            for node_i in dag.nodes():
                dag.nodes[node_i][property_name] = Util.random_choice(option)
        else:
            for src_i, tgt_i in dag.edges():
                dag.edges[src_i, tgt_i][property_name] = Util.random_choice(option)
