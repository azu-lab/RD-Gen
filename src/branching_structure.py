"""Nesting structure of the branching constructs of a DAG.

Everything is derived from the exported node/edge attributes alone
(``node_type``, ``branch_unit_id``, ``branch_id``, ``firing_prob``), so the
validator, the property setters and the evaluation scripts share one view of
which nodes belong to which branch.
"""
from collections import defaultdict
from typing import Dict, Hashable, List, Optional, Set, Tuple

import networkx as nx

# None: outside every construct. (unit, branch_id): directly inside that branch.
Region = Optional[Tuple[int, int]]


class BranchingConstraintError(Exception):
    """Raised when a DAG violates Melani Def III.1 or Zhao p-DAG constraints."""


class BranchingStructure:
    """Units, branch bodies and their nesting, plus the aggregates built on them."""

    ACCOUNTING_MODES = ("all", "expected", "max-branch")

    def __init__(self, dag: nx.DiGraph) -> None:
        self._dag = dag
        self.vent: Dict[int, int] = {}
        self.vext: Dict[int, int] = {}
        self.heads: Dict[int, Dict[int, int]] = {}
        self.firing_prob: Dict[int, Dict[int, Optional[float]]] = {}
        # bodies[u][b]: nodes reachable from head b of unit u without passing v_ext(u).
        self.bodies: Dict[int, Dict[int, Set[int]]] = {}
        self.parent: Dict[int, Region] = {}
        self.unit_depth: Dict[int, int] = {}
        self.region: Dict[int, Region] = {}
        self.children: Dict[Region, List[int]] = defaultdict(list)
        self._region_prob: Dict[Region, float] = {None: 1.0}
        self._collect_units()
        self._collect_branches()
        self._nest()

    @property
    def units(self) -> List[int]:
        return sorted(self.vent)

    @property
    def nesting_depth(self) -> int:
        return max(self.unit_depth.values(), default=0)

    # ---------- construction ----------

    def _collect_units(self) -> None:
        for n, attr in self._dag.nodes(data=True):
            t = attr.get("node_type", "regular")
            if t not in ("v_ent", "v_ext"):
                continue
            uid = attr.get("branch_unit_id")
            if uid is None:
                raise BranchingConstraintError(f"node {n} of type {t} has no branch_unit_id")
            table = self.vent if t == "v_ent" else self.vext
            if uid in table:
                raise BranchingConstraintError(f"unit {uid} has more than one {t}")
            table[uid] = n
        unpaired = set(self.vent) ^ set(self.vext)
        if unpaired:
            raise BranchingConstraintError(
                f"units without a matching v_ent/v_ext pair: {sorted(unpaired)}"
            )

    def _collect_branches(self) -> None:
        for uid in self.units:
            vent, vext = self.vent[uid], self.vext[uid]
            heads: Dict[int, int] = {}
            probs: Dict[int, Optional[float]] = {}
            bodies: Dict[int, Set[int]] = {}
            for _, head, d in self._dag.out_edges(vent, data=True):
                bid = d.get("branch_id")
                if bid is None:
                    raise BranchingConstraintError(
                        f"unit {uid}: v_ent out-edge ({vent}, {head}) has no branch_id"
                    )
                if bid in heads:
                    raise BranchingConstraintError(
                        f"unit {uid}: branch_id {bid} appears on two v_ent out-edges"
                    )
                heads[bid] = head
                probs[bid] = d.get("firing_prob")
                bodies[bid] = self._reach_until(head, vext)
            self.heads[uid], self.firing_prob[uid], self.bodies[uid] = heads, probs, bodies

    def _reach_until(self, start: int, stop: int) -> Set[int]:
        if start == stop:
            return set()
        seen = {start}
        stack = [start]
        while stack:
            u = stack.pop()
            for v in self._dag.successors(u):
                if v != stop and v not in seen:
                    seen.add(v)
                    stack.append(v)
        return seen

    def _nest(self) -> None:
        containing: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        for uid in self.units:
            for bid, body in self.bodies[uid].items():
                for v in body:
                    containing[v].append((uid, bid))
        for uid in self.units:
            self.unit_depth[uid] = 1 + len(containing[self.vent[uid]])

        def innermost(regions: List[Tuple[int, int]]) -> Region:
            if not regions:
                return None
            regions = sorted(regions, key=lambda r: self.unit_depth[r[0]])
            if len(regions) > 1 and (
                self.unit_depth[regions[-1][0]] == self.unit_depth[regions[-2][0]]
            ):
                raise BranchingConstraintError(
                    f"branches {regions[-2]} and {regions[-1]} overlap without nesting"
                )
            return regions[-1]

        for uid in self.units:
            vent, vext = self.vent[uid], self.vext[uid]
            if set(containing[vent]) != set(containing[vext]):
                raise BranchingConstraintError(
                    f"unit {uid}: v_ent and v_ext lie in different branches"
                )
            parent = innermost(containing[vent])
            if parent is not None:
                outer = self.bodies[parent[0]][parent[1]]
                for body in self.bodies[uid].values():
                    if not body <= outer:
                        raise BranchingConstraintError(
                            f"unit {uid} is not properly nested inside branch {parent}"
                        )
            self.parent[uid] = parent
            self.children[parent].append(uid)
            self.region[vent] = parent
            self.region[vext] = parent
        for v in self._dag.nodes():
            if v not in self.region:
                self.region[v] = innermost(containing[v])

    # ---------- probabilities ----------

    def region_prob(self, region: Region) -> float:
        """Probability that one release executes the nodes directly in ``region``."""
        if region not in self._region_prob:
            uid, bid = region
            p = self.firing_prob[uid][bid]
            if p is None:
                raise ValueError(f"unit {uid} carries no firing_prob (deterministic firing)")
            self._region_prob[region] = self.region_prob(self.parent[uid]) * p
        return self._region_prob[region]

    def marginal_prob(self, node: int) -> float:
        return self.region_prob(self.region[node])

    # ---------- aggregates ----------

    def aggregate(self, weights: Dict[Hashable, float], mode: str) -> float:
        """Aggregate node or edge weights over the branching structure.

        Keys are nodes or ``(src, dst)`` edges; elements not in ``weights`` count
        as 0. ``all`` sums every element, ``expected`` weights each element by
        its marginal execution probability, ``max-branch`` keeps the heaviest
        branch of every unit (Zhao 2025, Eq. (10), applied recursively).
        """
        if mode not in self.ACCOUNTING_MODES:
            raise ValueError(f"unknown accounting mode: {mode}")
        region_sum: Dict[Region, float] = defaultdict(float)
        for key, w in weights.items():
            region_sum[self._region_of(key)] += w
        return region_sum[None] + sum(
            self._unit_value(u, region_sum, mode) for u in self.children[None]
        )

    def _region_of(self, key: Hashable) -> Region:
        if isinstance(key, tuple):
            ra, rb = self.region[key[0]], self.region[key[1]]
            return ra if self._depth(ra) >= self._depth(rb) else rb
        return self.region[key]

    def _depth(self, region: Region) -> int:
        return 0 if region is None else self.unit_depth[region[0]]

    def _unit_value(self, uid: int, region_sum: Dict[Region, float], mode: str) -> float:
        values = {
            bid: region_sum[(uid, bid)]
            + sum(self._unit_value(c, region_sum, mode) for c in self.children[(uid, bid)])
            for bid in self.heads[uid]
        }
        if mode == "all":
            return sum(values.values())
        if mode == "max-branch":
            return max(values.values(), default=0.0)
        probs = self.firing_prob[uid]
        if any(p is None for p in probs.values()):
            raise ValueError(f"unit {uid} carries no firing_prob (deterministic firing)")
        return sum(probs[bid] * v for bid, v in values.items())
