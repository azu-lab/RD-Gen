import random
import sys
from logging import getLogger
from typing import List, Optional

import networkx as nx

from ..common import Util
from ..config import Config
from ..dag_builder import ChainBasedDAG
from .property_setter_base import PropertySetterBase

logger = getLogger(__name__)


class UtilizationSetter(PropertySetterBase):
    """Utilization setter class.

    Notes
    -----
    If both 'Period' and 'Execution time' are specified,
    'Execution time' is determined based on utilization and period
    (i.e., the range of 'Execution time' specified is ignored).
    The minimum value of 'Execution time' is 1 and never 0.

    """

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def _validate_config(self, config: Config) -> None:
        period = config.period
        execution_time = config.execution_time
        if period and execution_time:
            logger.warning(
                "Both 'Period' and 'Execution time' are specified, "
                "but 'Execution time' is determined based on utilization and period. "
                "So, the range of 'Execution time' entered is ignored."
            )

    def set(self, dag: nx.DiGraph) -> None:
        """Set period and execution time based on utilization.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.

        Notes
        -----
        If a chain-based DAG is entered 'Periodic type' is 'Chain',
        the chain utilization is used (see https://par.nsf.gov/servlets/purl/10276465).

        """
        total_utilization = self._config.total_utilization
        is_chain_case = isinstance(dag, ChainBasedDAG) and Util.ambiguous_equals(
            self._config.periodic_type, "chain"
        )
        if is_chain_case:
            if total_utilization:
                self._set_by_total_utilization_chain(dag)
            else:
                self._set_by_only_max_utilization_chain(dag)
        else:
            if total_utilization:
                self._set_by_total_utilization(dag)
            else:
                self._set_by_only_max_utilization(dag)

        # Set remain execution times
        for node_i in dag.nodes:
            if not dag.nodes[node_i].get("execution_time"):
                dag.nodes[node_i]["execution_time"] = Util.random_choice(
                    self._config.execution_time
                )

    def _set_by_total_utilization(self, dag: nx.DiGraph) -> None:
        """Set period and execution time based on total utilization.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.

        """
        timer_driven_nodes = self._get_timer_driven_nodes(dag)
        utilizations = self._UUniFast(
            Util.random_choice(self._config.total_utilization),
            len(timer_driven_nodes),
            self._config.maximum_utilization,
        )

        for timer_i, utilization in zip(timer_driven_nodes, utilizations):
            selected_period = self._choice_period(dag, timer_i)
            dag.nodes[timer_i]["period"] = selected_period
            exec = int(utilization * selected_period)
            if exec == 0:
                self._output_round_up_warning("Execution time", "Utilization")
                exec = 1
            dag.nodes[timer_i]["execution_time"] = exec

    def _set_by_total_utilization_chain(self, chain_based_dag: ChainBasedDAG) -> None:
        timer_driven_nodes = self._get_timer_driven_nodes(chain_based_dag)
        utilizations = self._UUniFast(
            Util.random_choice(self._config.total_utilization),
            len(timer_driven_nodes),
            self._config.maximum_utilization,
        )

        for chain in chain_based_dag.chains:
            selected_period = self._choice_period(chain_based_dag, chain.head)
            chain_based_dag.nodes[chain.head]["period"] = selected_period
            utilization = utilizations[timer_driven_nodes.index(chain.head)]
            sum_exec = int(utilization * selected_period)
            exec_grouping = self._grouping(sum_exec, chain.number_of_nodes())  # type: ignore
            if not exec_grouping:
                self._output_round_up_warning("Execution time", "Utilization")
                exec_grouping = [1 for _ in range(chain.number_of_nodes())]
            for node_i, exec in zip(chain.nodes, exec_grouping):
                chain_based_dag.nodes[node_i]["execution_time"] = exec

    def _set_by_only_max_utilization(self, dag: nx.DiGraph) -> None:
        """Set period and execution time randomly by only maximum utilization.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.

        Notes
        -----
        If 'Maximum utilization' is not specified,
        'Maximum utilization' is set to 1.0.

        """
        max_u = self._config.maximum_utilization or 1.0
        for node_i in self._get_timer_driven_nodes(dag):
            selected_period = self._choice_period(dag, node_i)
            dag.nodes[node_i]["period"] = selected_period
            min_u = 1 / selected_period  # Ensure 'Execution time' is at least 1.
            if min_u > max_u:
                self._output_round_up_warning("Execution time", "Utilization")
                exec = 1
            else:
                utilization = random.uniform(min_u, max_u)
                exec = int(utilization * selected_period)
            dag.nodes[node_i]["execution_time"] = exec

    def _set_by_only_max_utilization_chain(self, chain_based_dag: ChainBasedDAG) -> None:
        """Set period and execution time randomly by only maximum utilization.

        Parameters
        ----------
        chain_based_dag: ChainBasedDAG
            Chain-based DAG.

        Notes
        -----
        If 'Maximum utilization' is not specified,
        'Maximum utilization' is set to 1.0.

        """
        max_u = self._config.maximum_utilization or 1.0
        for chain in chain_based_dag.chains:
            selected_period = self._choice_period(chain_based_dag, chain.head)
            chain_based_dag.nodes[chain.head]["period"] = selected_period
            min_u = (
                chain.number_of_nodes() / selected_period
            )  # Ensure 'Execution time' is at least 1.
            if min_u > max_u:
                self._output_round_up_warning("Execution time", "Utilization")
                exec_grouping = [1 for _ in range(chain.number_of_nodes())]
            else:
                utilization = random.uniform(min_u, max_u)
                sum_exec = int(utilization * selected_period)
                exec_grouping = self._grouping(sum_exec, chain.number_of_nodes())  # type: ignore
                if not exec_grouping:
                    self._output_round_up_warning("Execution time", "Utilization")
                    exec_grouping = [1 for _ in range(chain.number_of_nodes())]
            for node_i, exec in zip(chain.nodes, exec_grouping):
                chain_based_dag.nodes[node_i]["execution_time"] = exec

    @staticmethod
    def _UUniFast(total_u: float, n: int, max_u: Optional[float] = None) -> List[float]:
        """Determine utilization based on UUniFast method.

        For detail, see https://idp.springer.com/authorize/casa?redirect_uri=https://link.springer.com/content/pdf/10.1007/s11241-005-0507-9.pdf&casa_token=ILaVXw6_1aUAAAAA:KEgQ8Iv70JXyNHj7hs11YvW2KRIPm89ab_1bILtRZFI5sBU1A7QGYaNDMshx4up16pA4W2gDohyAQmJqWyc.

        Parameters
        ----------
        total_u : float
            Total utilization.
        n : int
            Number of elements to distribute utilization.
        max_u : float
            Maximum utilization, by default None.

        Returns
        -------
        List[float]
            List of utilizations.

        Notes
        -----
        - If both 'Total utilization' and 'Maximum utilization' cannot be met,
          ignore 'Total utilization' and set each utilization to 'Maximum utilization'.
        - If $'total_u' / 'n' \simeq 'max_u'$,
          it takes an enormous amount of time to distribute them.
          Therefore, if the number of attempts exceeds the threshold,
          the utilization is distributed equally.

        """
        if max_u:
            if (total_u / n) >= max_u:
                logger.warning(
                    "Only either 'Total utilization' or 'Maximum utilization' can be satisfied."
                    "Therefore, 'Total utilization' is ignored "
                    "and each utilization is set to 'Maximum utilization'."
                    "To prevent this, it is recommended to reduce 'Total utilization', "
                    "increase 'Maximum utilization', or increase the number of nodes."
                )
                utilizations = [max_u for _ in range(n)]
            else:
                utilizations = UtilizationSetter._UUniFast_with_max_u(total_u, n, max_u)

        else:  # Original UUniFast method
            remain_u = total_u
            utilizations: List[float] = []  # type: ignore
            for i in range(n - 1):
                next_u = -sys.maxsize
                next_u = remain_u * (random.uniform(0, 1) ** (1 / (n - i)))
                utilizations.append(remain_u - next_u)
                remain_u = next_u
            utilizations.append(remain_u)

        return utilizations

    @staticmethod
    def _UUniFast_with_max_u(total_u: float, n: int, max_u: float) -> List[float]:
        """Determine utilization based on UUniFast method not to exceed 'max_u'.

        Parameters
        ----------
        total_u : float
            Total utilization.
        n : int
            Number of elements to distribute utilization.
        max_u : float
            Maximum utilization.

        Returns
        -------
        List[float]
            List of utilizations.

        Notes
        -----
        If $'total_u' / 'n' \simeq 'max_u'$,
        it takes an enormous amount of time to distribute them.
        Therefore, if the number of attempts exceeds the threshold,
        the utilization is distributed equally.

        """
        max_try = 100  # HACK
        for try_i in range(1, max_try + 1):
            remain_u = total_u
            utilizations: List[float] = []
            for i in range(n - 1):
                next_u = -sys.maxsize
                while remain_u - next_u >= max_u:
                    next_u = remain_u * (random.uniform(0, 1) ** (1 / (n - i)))
                utilizations.append(remain_u - next_u)
                remain_u = next_u

            if remain_u < max_u:
                utilizations.append(remain_u)
                break

            if try_i == max_try:
                # HACK: Distribute equally.
                utilizations = [total_u / n for _ in range(n)]

        return utilizations

    def _choice_period(self, dag: nx.DiGraph, node_i: int) -> int:
        if self._config.source_node_period and node_i in Util.get_source_nodes(dag):
            return Util.random_choice(self._config.source_node_period)
        if self._config.exit_node_period and node_i in Util.get_exit_nodes(dag):
            return Util.random_choice(self._config.exit_node_period)
        return Util.random_choice(self._config.period)

    def _get_timer_driven_nodes(self, dag: nx.DiGraph) -> List[int]:
        """Get indices of timer-driven nodes according to 'Periodic type'.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.

        Returns
        -------
        List[int]
            List of indexes of timer-driven nodes.

        """
        periodic_type = self._config.periodic_type
        timer_driven_nodes: List[int]
        if Util.ambiguous_equals(periodic_type, "All"):
            timer_driven_nodes = list(dag.nodes())
        elif Util.ambiguous_equals(periodic_type, "IO"):
            timer_driven_nodes = list(set(Util.get_source_nodes(dag) + Util.get_exit_nodes(dag)))
        elif Util.ambiguous_equals(periodic_type, "Entry"):
            timer_driven_nodes = Util.get_source_nodes(dag)
        elif isinstance(dag, ChainBasedDAG) and Util.ambiguous_equals(periodic_type, "Chain"):
            timer_driven_nodes = dag.chain_heads

        return timer_driven_nodes
