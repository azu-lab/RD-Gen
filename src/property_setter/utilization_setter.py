import random
import sys
from logging import getLogger
from typing import List, Optional

import networkx as nx

from ..branching_structure import BranchingStructure
from ..common import Util
from ..config import Config
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

    'Periodic type' selects the timer-driven nodes and the quantity that
    'Total utilization' controls:

    - All / IO / Entry: every timer-driven node gets its own period and a
      UUniFast share of the utilization.
    - Chain: every chain head gets a period; the chain's aggregate execution
      time C_Gamma = u_Gamma * T_Gamma is split over the chain's nodes.
    - DAG: one period T shared by the whole DAG (stored on the source nodes and
      in ``dag.graph["period"]``); the aggregate execution time U * T is split
      over all regular nodes.

    For chains and DAGs that contain branching constructs the aggregate follows
    'Accounting' (all / expected / max-branch, see BranchingStructure.aggregate).
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
        if Util.ambiguous_equals(config.periodic_type, "DAG") and (
            config.source_node_period or config.sink_node_period
        ):
            logger.warning(
                "'Periodic type: DAG' uses a single 'Period' for the whole DAG; "
                "'Source node period' and 'Sink node period' are ignored."
            )

    def set(self, dag: nx.DiGraph) -> None:
        """Set period and execution time based on utilization.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.

        """
        periodic_type = self._config.periodic_type
        total_utilization = self._config.total_utilization
        if Util.ambiguous_equals(periodic_type, "chain"):
            if total_utilization:
                self._set_by_total_utilization_chain(dag)
            else:
                self._set_by_only_max_utilization_chain(dag)
        elif Util.ambiguous_equals(periodic_type, "DAG"):
            if total_utilization:
                self._set_by_total_utilization_dag(dag)
            else:
                self._set_by_only_max_utilization_dag(dag)
        else:
            if total_utilization:
                self._set_by_total_utilization(dag)
            else:
                self._set_by_only_max_utilization(dag)

        # Set remain execution times
        for node_i in Util.regular_nodes(dag):
            if not dag.nodes[node_i].get("execution_time"):
                dag.nodes[node_i]["execution_time"] = Util.random_choice(
                    self._config.execution_time
                )

    # ---------- All / IO / Entry ----------

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

    # ---------- Chain ----------

    def _set_by_total_utilization_chain(self, dag: nx.DiGraph) -> None:
        chains = Util.chains(dag)
        utilizations = self._UUniFast(
            Util.random_choice(self._config.total_utilization),
            len(chains),
            self._config.maximum_utilization,
        )
        for chain_nodes, utilization in zip(chains.values(), utilizations):
            head = Util.chain_head(dag, chain_nodes)
            selected_period = self._choice_period(dag, head)
            dag.nodes[head]["period"] = selected_period
            self._distribute_execution_time(dag, chain_nodes, int(utilization * selected_period))

    def _set_by_only_max_utilization_chain(self, dag: nx.DiGraph) -> None:
        """Set period and execution time randomly by only maximum utilization.

        Parameters
        ----------
        dag : nx.DiGraph
            Chain-based DAG (nodes carry ``chain_id``).

        Notes
        -----
        If 'Maximum utilization' is not specified,
        'Maximum utilization' is set to 1.0.

        """
        max_u = self._config.maximum_utilization or 1.0
        for chain_nodes in Util.chains(dag).values():
            head = Util.chain_head(dag, chain_nodes)
            selected_period = self._choice_period(dag, head)
            dag.nodes[head]["period"] = selected_period
            num_regular = len([n for n in chain_nodes if self._is_regular(dag, n)])
            self._distribute_execution_time(
                dag, chain_nodes, self._sample_aggregate(num_regular, selected_period, max_u)
            )

    # ---------- DAG ----------

    def _set_by_total_utilization_dag(self, dag: nx.DiGraph) -> None:
        selected_period = self._set_dag_period(dag)
        utilization = self._UUniFast(
            Util.random_choice(self._config.total_utilization),
            1,
            self._config.maximum_utilization,
        )[0]
        self._distribute_execution_time(
            dag, list(dag.nodes()), int(utilization * selected_period)
        )

    def _set_by_only_max_utilization_dag(self, dag: nx.DiGraph) -> None:
        selected_period = self._set_dag_period(dag)
        max_u = self._config.maximum_utilization or 1.0
        self._distribute_execution_time(
            dag,
            list(dag.nodes()),
            self._sample_aggregate(len(Util.regular_nodes(dag)), selected_period, max_u),
        )

    def _set_dag_period(self, dag: nx.DiGraph) -> int:
        selected_period = Util.random_choice(self._config.period)
        dag.graph["period"] = selected_period
        for source_i in Util.get_source_nodes(dag):
            dag.nodes[source_i]["period"] = selected_period
        return selected_period

    # ---------- common ----------

    @staticmethod
    def _is_regular(dag: nx.DiGraph, node_i: int) -> bool:
        return dag.nodes[node_i].get("node_type", "regular") == "regular"

    def _sample_aggregate(self, num_regular: int, period: int, max_u: float) -> int:
        """Aggregate execution time for u ~ U(min_u, max_u), each node needing C >= 1."""
        min_u = num_regular / period
        if min_u > max_u:
            self._output_round_up_warning("Execution time", "Utilization")
            return num_regular
        return int(random.uniform(min_u, max_u) * period)

    def _distribute_execution_time(self, dag: nx.DiGraph, nodes: List[int], target: int) -> None:
        """Split ``target`` over the regular nodes of ``nodes`` so that the aggregate
        selected by 'Accounting' equals ``target``.

        'all' (or no branching construct among ``nodes``) partitions ``target``
        randomly, so the sum is exact. 'expected' / 'max-branch' draw raw execution
        times ('Execution time' if given, else U(0, 1)) and scale them so that the
        aggregate hits ``target`` up to integer rounding.
        """
        regulars = [n for n in nodes if self._is_regular(dag, n)]
        mode = self._config.branching_accounting
        has_units = any(dag.nodes[n].get("node_type") == "v_ent" for n in nodes)
        if mode == "all" or not has_units:
            grouping = self._grouping(target, len(regulars))
            if not grouping:
                self._output_round_up_warning("Execution time", "Utilization")
                grouping = [1 for _ in regulars]
            for node_i, exec in zip(regulars, grouping):
                dag.nodes[node_i]["execution_time"] = exec
            return

        if target < len(regulars):
            self._output_round_up_warning("Execution time", "Utilization")
        execution_time = self._config.execution_time
        raw = {
            n: (Util.random_choice(execution_time) if execution_time else random.random())
            for n in regulars
        }
        aggregate = BranchingStructure(dag).aggregate(raw, mode)
        factor = target / aggregate if aggregate > 0 else 0.0
        for node_i in regulars:
            dag.nodes[node_i]["execution_time"] = max(1, round(raw[node_i] * factor))

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
        - If $'total_u' / 'n' \\simeq 'max_u'$,
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
        If $'total_u' / 'n' \\simeq 'max_u'$,
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
        if self._config.sink_node_period and node_i in Util.get_sink_nodes(dag):
            return Util.random_choice(self._config.sink_node_period)
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
        if Util.ambiguous_equals(periodic_type, "All"):
            return Util.regular_nodes(dag)
        if Util.ambiguous_equals(periodic_type, "DAG"):
            return Util.get_source_nodes(dag)
        if Util.ambiguous_equals(periodic_type, "Chain"):
            return [Util.chain_head(dag, nodes) for nodes in Util.chains(dag).values()]
        raise ValueError(f"unknown 'Periodic type': {periodic_type}")
