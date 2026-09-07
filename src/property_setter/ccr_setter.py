import random
from logging import getLogger
from typing import Dict, Hashable, List, Optional, Tuple

import networkx as nx

from ..branching_structure import BranchingStructure
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
        # With branching constructs, CCR = Agg(comm) / Agg(exec) where Agg follows
        # 'Accounting' (all / expected / max-branch); without them all modes coincide.
        structure = None
        if self._config.branching_accounting != "all" and any(
            a.get("node_type") == "v_ent" for _, a in dag.nodes(data=True)
        ):
            structure = BranchingStructure(dag)
        if self._config.execution_time:
            self._set_by_exec(dag, ccr, structure)
        else:
            self._set_by_comm(dag, ccr, structure)

    @staticmethod
    def _regular_edges(dag: nx.DiGraph) -> List[Tuple[int, int]]:
        return [
            (s, t) for s, t in dag.edges()
            if (dag.nodes[s].get("node_type", "regular") == "regular"
                and dag.nodes[t].get("node_type", "regular") == "regular")
        ]

    def _aggregate(self, weights: Dict[Hashable, int], structure: Optional[BranchingStructure]):
        if structure is None:
            return sum(weights.values())
        return structure.aggregate(weights, self._config.branching_accounting)

    def _distribute(self, dag: nx.DiGraph, keys: list, target: int, attr: str, option,
                    structure: Optional[BranchingStructure], error_param: str) -> None:
        """Assign ``attr`` to nodes or edges ``keys`` so that their aggregate is ``target``.

        Without a structure the target is partitioned randomly (exact sum); with one,
        raw values (``option`` if given, else U(0, 1)) are scaled to the target.
        """
        store = dag.nodes if attr == "execution_time" else dag.edges
        if not keys:
            return
        if structure is None:
            grouping = self._grouping(target, len(keys))
            if not grouping:
                self._output_round_up_warning(error_param, "CCR")
                grouping = [1 for _ in keys]
            for key, value in zip(keys, grouping):
                store[key][attr] = value
            return
        raw = {k: (Util.random_choice(option) if option else random.random()) for k in keys}
        aggregate = self._aggregate(raw, structure)
        factor = target / aggregate if aggregate > 0 else 0.0
        for key in keys:
            store[key][attr] = max(1, round(raw[key] * factor))

    def _set_by_exec(self, dag: nx.DiGraph, ccr: float,
                     structure: Optional[BranchingStructure]) -> None:
        execs = {}
        for node_i in Util.regular_nodes(dag):
            execs[node_i] = Util.random_choice(self._config.execution_time)
            dag.nodes[node_i]["execution_time"] = execs[node_i]
        sum_comm = int(ccr * self._aggregate(execs, structure))
        self._distribute(dag, self._regular_edges(dag), sum_comm, "communication_time",
                         self._config.communication_time, structure, "Communication time")

    def _set_by_comm(self, dag: nx.DiGraph, ccr: float,
                     structure: Optional[BranchingStructure]) -> None:
        comms = {}
        for edge in self._regular_edges(dag):
            comms[edge] = Util.random_choice(self._config.communication_time)
            dag.edges[edge]["communication_time"] = comms[edge]
        sum_exec = int(self._aggregate(comms, structure) / ccr)
        self._distribute(dag, Util.regular_nodes(dag), sum_exec, "execution_time",
                         self._config.execution_time, structure, "Execution time")
