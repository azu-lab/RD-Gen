import math
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
        if config.whole_dag_utilization and Util.ambiguous_equals(config.periodic_type, "chain"):
            logger.warning(
                "'Whole-DAG utilization' is not supported together with "
                "'Periodic type: Chain'; it will be ignored."
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

        If 'Auto-fit cycle' is enabled (only takes effect together with
        'Total utilization' on a non-chain DAG), the execution times of the
        non-timer-driven nodes are drawn *before* periods are chosen, so
        that the downstream critical path length is already known when a
        timer-driven node's period is picked. This lets the period be grown
        (up to the configured maximum) just enough to keep the target
        utilization feasible, instead of leaving it to chance. See
        '_set_by_total_utilization' for the actual adjustment.

        If 'Whole-DAG utilization' is specified (and 'Periodic type' is not
        'Chain'), it takes priority over 'Total utilization' /
        'Maximum utilization': the DAG's *total* workload (summed over all
        regular nodes, not just a timer-driven one) is sized against a
        single shared period, allowing utilization >= 1. See
        '_set_by_whole_dag_utilization'.

        """
        total_utilization = self._config.total_utilization
        whole_dag_utilization = self._config.whole_dag_utilization
        is_chain_case = isinstance(dag, ChainBasedDAG) and Util.ambiguous_equals(
            self._config.periodic_type, "chain"
        )
        auto_adjust = bool(self._config.auto_fit_cycle) and total_utilization and not is_chain_case

        if whole_dag_utilization and not is_chain_case:
            self._set_by_whole_dag_utilization(dag)
            return

        if auto_adjust:
            timer_driven_nodes = set(self._get_timer_driven_nodes(dag))
            for node_i in Util.regular_nodes(dag):
                if node_i not in timer_driven_nodes and not dag.nodes[node_i].get("execution_time"):
                    dag.nodes[node_i]["execution_time"] = Util.random_choice(
                        self._config.execution_time
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
        for node_i in Util.regular_nodes(dag):
            if not dag.nodes[node_i].get("execution_time"):
                dag.nodes[node_i]["execution_time"] = Util.random_choice(
                    self._config.execution_time
                )

    def _set_by_whole_dag_utilization(self, dag: nx.DiGraph) -> None:
        """Set a single shared period and distribute the DAG's *total*
        workload (the sum of every node's execution time) across all
        regular nodes via UUniFast, so that
        (sum of execution times) / period == target utilization.

        Unlike '_set_by_total_utilization' (which only sizes a single
        timer-driven node's own execution time), this allows the target
        utilization to exceed 1, which is what Federated-style heavy/light
        classification needs. It does not attempt to widen the graph or
        adjust the period for feasibility: whether a critical path stays
        under the period depends on how the random UUniFast split lands
        and how much parallel width the DAG structure provides.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.

        """
        timer_driven_nodes = self._get_timer_driven_nodes(dag)
        selected_period = self._choice_period(dag, timer_driven_nodes[0])
        for timer_i in timer_driven_nodes:
            dag.nodes[timer_i]["period"] = selected_period

        regular_nodes = Util.regular_nodes(dag)
        utilizations = self._UUniFast(
            Util.random_choice(self._config.whole_dag_utilization),
            len(regular_nodes),
            self._config.maximum_utilization,
        )

        exec_times = self._distribute_execution_times(
            utilizations, selected_period, self._config.maximum_utilization
        )
        for node_i, exec in zip(regular_nodes, exec_times):
            dag.nodes[node_i]["execution_time"] = exec

    def _distribute_execution_times(
        self, utilizations: List[float], period: int, max_utilization: Optional[float] = None
    ) -> List[int]:
        """Convert per-node utilization shares into integer execution
        times via the largest-remainder method, instead of truncating
        each node independently with 'int(u_i * period)'.

        Parameters
        ----------
        utilizations : List[float]
            Per-node utilization shares (as returned by '_UUniFast').
        period : int
            Shared period.
        max_utilization : float, optional
            Per-node utilization cap; a node is never bumped past
            'floor(max_utilization * period)', by default None.

        Returns
        -------
        List[int]
            Integer execution times, one per input utilization.

        Notes
        -----
        Independently truncating every node (the naive approach) always
        rounds *down*, so the resulting total drifts below the target by
        roughly 0.5 per node on average. That drift is not just cosmetic:
        near a classification threshold that depends on total utilization
        (e.g. Federated's heavy/light split at utilization == 1), it can
        silently flip which side of the threshold a generated DAG actually
        lands on even though its configured target was on the other side.

        The largest-remainder method instead floors every node, then
        hands out the leftover units (the difference between the rounded
        target total and the sum of floors) one at a time to the nodes
        with the largest fractional remainder, skipping any node already
        at 'max_utilization'. This makes the total match the target as
        closely as integer execution times allow, with no systematic
        directional bias.

        """
        raw = [u * period for u in utilizations]
        floor_vals = [int(r) for r in raw]
        remainders = [r - f for r, f in zip(raw, floor_vals)]
        target_total = round(sum(raw))
        deficit = target_total - sum(floor_vals)

        cap = max_utilization * period if max_utilization else None

        exec_vals = floor_vals[:]
        order = sorted(range(len(raw)), key=lambda i: remainders[i], reverse=True)
        for idx in order:
            if deficit <= 0:
                break
            if cap is not None and exec_vals[idx] + 1 > cap + 1e-9:
                continue
            exec_vals[idx] += 1
            deficit -= 1

        for i, exec_i in enumerate(exec_vals):
            if exec_i == 0:
                self._output_round_up_warning("Execution time", "Utilization")
                exec_vals[i] = 1

        return exec_vals

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
            if self._config.auto_fit_cycle and utilization < 1:
                selected_period = self._adjust_period_for_feasibility(
                    dag, timer_i, utilization, selected_period
                )
            dag.nodes[timer_i]["period"] = selected_period
            exec = int(utilization * selected_period)
            if exec == 0:
                self._output_round_up_warning("Execution time", "Utilization")
                exec = 1
            dag.nodes[timer_i]["execution_time"] = exec

    def _adjust_period_for_feasibility(
        self, dag: nx.DiGraph, timer_i: int, utilization: float, selected_period: int
    ) -> int:
        """Grow 'selected_period' (up to the configured maximum) so that the
        downstream critical path still fits once 'timer_i' consumes
        'utilization' of the period, preserving the target utilization
        exactly (i.e. the execution time is still 'utilization * period').

        Parameters
        ----------
        dag : nx.DiGraph
            DAG. Non-timer-driven nodes reachable from 'timer_i' must
            already have 'execution_time' set (see 'set').
        timer_i : int
            Timer-driven node whose period is being chosen.
        utilization : float
            Target utilization for 'timer_i', already known to be < 1.
        selected_period : int
            Period randomly drawn from the configured range.

        Returns
        -------
        int
            'selected_period', or a larger value (capped at the configured
            maximum period for 'timer_i') if that was needed to keep the
            downstream critical path length within reach of the deadline.

        Notes
        -----
        This is a heuristic sizing based on execution times only: any
        'Communication time' added by a later property setter is not yet
        known here, so a residual chance of infeasibility remains. The
        feasibility check in 'DeadlineSetter' (which runs after
        'Communication time' has been set) is the authoritative guard and
        must stay in place regardless of this adjustment.

        """
        dag.nodes[timer_i]["execution_time"] = 0
        l_rest = max(
            (
                Util.get_critical_path_length(dag, timer_i, exit_i)
                for exit_i in Util.get_sink_nodes(dag)
            ),
            default=0,
        )
        del dag.nodes[timer_i]["execution_time"]

        if l_rest == 0:
            return selected_period

        required_period = math.ceil(l_rest / (1 - utilization))
        period_cap = self._period_cap(dag, timer_i)
        return max(selected_period, min(required_period, period_cap))

    def _period_cap(self, dag: nx.DiGraph, node_i: int) -> int:
        if self._config.source_node_period and node_i in Util.get_source_nodes(dag):
            return Util.get_option_max(self._config.source_node_period)
        if self._config.sink_node_period and node_i in Util.get_sink_nodes(dag):
            return Util.get_option_max(self._config.sink_node_period)
        return Util.get_option_max(self._config.period)

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
        timer_driven_nodes: List[int]
        if Util.ambiguous_equals(periodic_type, "All"):
            timer_driven_nodes = Util.regular_nodes(dag)
        elif Util.ambiguous_equals(periodic_type, "IO"):
            timer_driven_nodes = list(set(Util.get_source_nodes(dag) + Util.get_sink_nodes(dag)))
        elif Util.ambiguous_equals(periodic_type, "Entry"):
            timer_driven_nodes = Util.get_source_nodes(dag)
        elif isinstance(dag, ChainBasedDAG) and Util.ambiguous_equals(periodic_type, "Chain"):
            timer_driven_nodes = dag.chain_heads

        return timer_driven_nodes
