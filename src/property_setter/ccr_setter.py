from logging import getLogger

import networkx as nx

from ..common import Util
from ..config import Config
from .property_setter_base import PropertySetterBase

logger = getLogger(__name__)


class CCRSetter(PropertySetterBase):
    """CCR setter class."""

    def __init__(self, config: Config) -> None:
        """Constructor.

        Parameters
        ----------
        config : Config
            Config.

        """
        super().__init__(config)

    def _validate_config(self, config: Config) -> None:
        execution_time = config.execution_time
        communication_time = config.communication_time
        if execution_time and communication_time:
            logger.warning(
                "Both 'Execution time' and 'Communication time' are specified, "
                "but 'Communication time' is determined based on 'Execution time' and 'CCR'. "
                "So, the range of 'Communication time' entered is ignored."
            )

    def set(self, dag: nx.DiGraph) -> None:
        """Set CCR.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.

        Notes
        -----
        If both 'Execution time' and 'Communication time' are specified,
        'Execution time' is given priority and
        'Communication time' is calculated based on 'Execution time' and 'CCR'
        (i.e., the range of 'Communication time' specified is ignored).

        """
        ccr = Util.random_choice(self._config.ccr)
        if self._config.execution_time:
            self._set_by_exec(dag, ccr)
        else:
            self._set_by_comm(dag, ccr)

    def _set_by_exec(self, dag: nx.DiGraph, ccr: float) -> None:
        # Set execution time
        sum_exec = 0
        for node_i in dag.nodes():
            exec = Util.random_choice(self._config.execution_time)
            dag.nodes[node_i]["execution_time"] = exec
            sum_exec += exec

        # Calculate sum_comm
        sum_comm = int(ccr * sum_exec)

        # Set communication time
        comm_grouping = self._grouping(sum_comm, dag.number_of_edges())
        if not comm_grouping:
            self._output_round_up_warning("Communication time", "CCR")
            comm_grouping = [1 for _ in range(dag.number_of_edges())]
        for edge, comm in zip(dag.edges(), comm_grouping):
            dag.edges[edge[0], edge[1]]["communication_time"] = comm

    def _set_by_comm(self, dag: nx.DiGraph, ccr: float) -> None:
        # Set communication time
        sum_comm = 0
        for src_i, tgt_i in dag.edges():
            comm = Util.random_choice(self._config.communication_time)
            dag.edges[src_i, tgt_i]["communication_time"] = comm
            sum_comm += comm

        # Calculate sum_exec
        sum_exec = int(sum_comm / ccr)

        # Set communication time
        exec_grouping = self._grouping(sum_exec, dag.number_of_nodes())
        if not exec_grouping:
            self._output_round_up_warning("Execution time", "CCR")
            exec_grouping = [1 for _ in range(dag.number_of_nodes())]
        for node_i, exec in zip(dag.nodes(), exec_grouping):
            dag.nodes[node_i]["execution_time"] = exec
