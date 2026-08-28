import random

import networkx as nx

from ..common import Util
from ..config import Config
from ..exceptions import BuildFailedError
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

        Notes
        -----
        The relationship enforced between the deadline D and the period T
        depends on 'Deadline mode':

        - 'Implicit': D = T. Raises BuildFailedError if L > T (i.e. the
          critical path alone already exceeds the period, making the
          instance infeasible for any scheduler regardless of D).
        - 'Constrained': D is drawn uniformly from (L, T], where L is the
          critical path length. Raises BuildFailedError if L >= T (i.e. the
          critical path alone already exceeds the period).
        - 'Arbitrary' (default when 'Deadline mode' is omitted):
          D = L * ratio, independent of T (legacy behavior).

        'Implicit' and 'Constrained' require 'Multi-rate' with
        'Periodic type: Entry' (enforced by ConfigValidator), so that every
        source node reaching a given sink carries a well-defined, single
        period. If sources reaching the same sink disagree on their period,
        BuildFailedError is raised for that DAG instance.

        """
        mode = self._config.deadline_mode
        is_arbitrary = Util.ambiguous_equals(mode, "arbitrary")

        for exit_i in Util.get_sink_nodes(dag):
            max_cp_len = 0
            reaching_periods = set()
            for entry_i in Util.get_source_nodes(dag):
                cp_len = self._get_cp_len(dag, entry_i, exit_i)
                if cp_len > max_cp_len:
                    max_cp_len = cp_len
                if cp_len > 0 and not is_arbitrary:
                    reaching_periods.add(dag.nodes[entry_i]["period"])

            if is_arbitrary:
                dag.nodes[exit_i]["end_to_end_deadline"] = int(
                    max_cp_len * Util.random_choice(self._config.ratio_of_deadline_to_critical_path)
                )
                continue

            if len(reaching_periods) != 1:
                raise BuildFailedError(
                    f"Deadline mode '{mode}' requires exactly one period among the "
                    f"source nodes reaching sink {exit_i}, but found {len(reaching_periods)}."
                )
            period = reaching_periods.pop()

            if Util.ambiguous_equals(mode, "implicit"):
                if max_cp_len > period:
                    raise BuildFailedError(
                        f"Implicit deadline is infeasible at sink {exit_i}: "
                        f"critical path length {max_cp_len} > period {period}."
                    )
                dag.nodes[exit_i]["end_to_end_deadline"] = period
            else:  # Constrained
                if max_cp_len >= period:
                    raise BuildFailedError(
                        f"Constrained deadline is infeasible at sink {exit_i}: "
                        f"critical path length {max_cp_len} >= period {period}."
                    )
                dag.nodes[exit_i]["end_to_end_deadline"] = int(
                    max_cp_len + random.uniform(0, 1) * (period - max_cp_len)
                )

    @staticmethod
    def _get_cp_len(dag: nx.DiGraph, source: int, exit: int) -> int:
        """Get critical path length from 'source' to 'exit'.

        Thin wrapper kept for backward compatibility; the implementation
        now lives in 'Util.get_critical_path_length' so it can be shared
        with 'UtilizationSetter' (used there to size periods that keep a
        target utilization feasible; see 'Auto-adjust period').

        """
        return Util.get_critical_path_length(dag, source, exit)
