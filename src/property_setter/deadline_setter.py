import networkx as nx

from ..common import Util
from ..config import Config
from .property_setter_base import PropertySetterBase


class DeadlineSetter(PropertySetterBase):
    """Deadline setter class."""

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
        """Set end-to-end deadline based on critical path length.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.

        """
        for exit_i in Util.get_sink_nodes(dag):
            max_cp_len = 0
            for entry_i in Util.get_source_nodes(dag):
                cp_len = self._get_cp_len(dag, entry_i, exit_i)
                if cp_len > max_cp_len:
                    max_cp_len = cp_len

            dag.nodes[exit_i]["end_to_end_deadline"] = int(
                max_cp_len * Util.random_choice(self._config.ratio_of_deadline_to_critical_path)
            )

    @staticmethod
    def _get_cp_len(dag: nx.DiGraph, source: int, exit: int) -> int:
        """Get critical path length.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.
        source : int
            Index of path source.
        exit : int
            Index of path exit.

        Returns
        -------
        int
            Critical path length.

        Notes
        -----
        If the edge has 'Communication time',
        'Communication time' is also included in critical path length.

        """
        cp_len = 0
        for path in nx.all_simple_paths(dag, source=source, target=exit):
            path_len = 0
            for i in range(len(path)):
                path_len += dag.nodes[path[i]]["execution_time"]
                if i != len(path) - 1 and dag.edges[path[i], path[i + 1]].get(
                    "communication_time"
                ):
                    path_len += dag.edges[path[i], path[i + 1]]["communication_time"]

            if path_len > cp_len:
                cp_len = path_len

        return cp_len
