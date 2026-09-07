from collections import defaultdict
from typing import Callable, Dict, Set

import networkx as nx

from .branching_structure import BranchingConstraintError, BranchingStructure


class BranchingValidator:
    """Verify cDAG / pDAG structural constraints from the output graph alone.

    Melani 2015 Def III.1 (cDAG):
      - The graph is acyclic.
      - Each branch_unit_id has exactly one v_ent and one v_ext.
      - branch_id values on v_ent out-edges are {0, 1, ..., k-1} with k >= 2.
      - Branch bodies of one unit are pairwise disjoint and properly nested in
        the enclosing branch.
      - No edge enters a body except v_ent -> head, and no edge leaves a body
        except into v_ext; every predecessor of v_ext lies in a body.
      - v_ent dominates and v_ext post-dominates every body node (checked
        independently with NetworkX dominator trees).

    Zhao 2025 p-DAG (only when firing == "probabilistic"):
      - Every v_ent out-edge carries firing_prob in [0, 1].
      - firing_prob values of one unit sum to 1 (within 1e-9).
    """

    _TOLERANCE = 1e-9

    @staticmethod
    def assert_valid(dag: nx.DiGraph, firing: str) -> BranchingStructure:
        if not nx.is_directed_acyclic_graph(dag):
            raise BranchingConstraintError("graph contains a cycle")
        structure = BranchingStructure(dag)
        BranchingValidator._check_branches(dag, structure)
        if structure.units:
            BranchingValidator._check_dominance(dag, structure)
        if firing == "probabilistic":
            BranchingValidator._check_firing_probabilities(structure)
        return structure

    @staticmethod
    def _check_branches(dag: nx.DiGraph, s: BranchingStructure) -> None:
        for uid in s.units:
            vent, vext = s.vent[uid], s.vext[uid]
            branch_ids = sorted(s.heads[uid])
            if len(branch_ids) < 2:
                raise BranchingConstraintError(f"unit {uid} has fewer than two branches")
            if branch_ids != list(range(len(branch_ids))):
                raise BranchingConstraintError(
                    f"unit {uid}: branch_id on v_ent out-edges must be "
                    f"{{0, ..., k-1}}; got {branch_ids}"
                )
            bodies = [s.bodies[uid][b] for b in branch_ids]
            for i in range(len(bodies)):
                for j in range(i + 1, len(bodies)):
                    overlap = bodies[i] & bodies[j]
                    if overlap:
                        raise BranchingConstraintError(
                            f"unit {uid}: branches {i} and {j} share vertices {overlap}"
                        )
            all_bodies: Set[int] = set().union(*bodies)
            for bid, body in zip(branch_ids, bodies):
                if not body:
                    raise BranchingConstraintError(f"unit {uid}: branch {bid} is empty")
                for v in body:
                    for p in dag.predecessors(v):
                        if p not in body and p != vent:
                            raise BranchingConstraintError(
                                f"unit {uid}: edge ({p}, {v}) enters branch {bid} "
                                "from outside"
                            )
                if not any(vext in dag.successors(v) for v in body):
                    raise BranchingConstraintError(
                        f"unit {uid}: branch {bid} never reaches v_ext {vext}"
                    )
            for p in dag.predecessors(vext):
                if p not in all_bodies:
                    raise BranchingConstraintError(
                        f"unit {uid}: edge ({p}, {vext}) reaches v_ext from outside the branches"
                    )

    @staticmethod
    def _check_dominance(dag: nx.DiGraph, s: BranchingStructure) -> None:
        dominates = BranchingValidator._dominance_test(dag, reverse=False)
        post_dominates = BranchingValidator._dominance_test(dag, reverse=True)
        for uid in s.units:
            vent, vext = s.vent[uid], s.vext[uid]
            body_nodes = set().union(*s.bodies[uid].values())
            for v in body_nodes | {vext}:
                if not dominates(vent, v):
                    raise BranchingConstraintError(
                        f"unit {uid}: v_ent {vent} does not dominate node {v}"
                    )
            for v in body_nodes | {vent}:
                if not post_dominates(vext, v):
                    raise BranchingConstraintError(
                        f"unit {uid}: v_ext {vext} does not post-dominate node {v}"
                    )

    @staticmethod
    def _dominance_test(dag: nx.DiGraph, reverse: bool) -> Callable[[int, int], bool]:
        """Return ``test(a, v)`` = "a (post-)dominates v", via NetworkX dominator trees.

        A virtual root above all sources (sinks when ``reverse``) turns the DAG into
        a single-entry flow graph; the tree is then labelled with Euler-tour
        intervals so that each ancestor test costs O(1).
        """
        h = nx.DiGraph()
        h.add_nodes_from(dag.nodes())
        h.add_edges_from((b, a) if reverse else (a, b) for a, b in dag.edges())
        root = object()
        roots = [n for n in h.nodes() if h.in_degree(n) == 0]
        h.add_edges_from((root, n) for n in roots)
        idom = nx.immediate_dominators(h, root)
        tree_children: Dict[object, list] = defaultdict(list)
        for v, d in idom.items():
            if v != root:
                tree_children[d].append(v)
        tin: Dict[object, int] = {}
        tout: Dict[object, int] = {}
        clock = 0
        stack = [(root, False)]
        while stack:
            v, leaving = stack.pop()
            if leaving:
                tout[v] = clock
            else:
                tin[v] = clock
                stack.append((v, True))
                stack.extend((c, False) for c in tree_children[v])
            clock += 1
        return lambda a, v: tin[a] <= tin[v] and tout[v] <= tout[a]

    @staticmethod
    def _check_firing_probabilities(s: BranchingStructure) -> None:
        for uid in s.units:
            total = 0.0
            for bid, p in s.firing_prob[uid].items():
                if p is None:
                    raise BranchingConstraintError(
                        f"unit {uid}: out-edge of v_ent {s.vent[uid]} (branch {bid}) "
                        "missing firing_prob"
                    )
                if not (0.0 <= p <= 1.0):
                    raise BranchingConstraintError(f"unit {uid}: firing_prob {p} out of [0, 1]")
                total += p
            if abs(total - 1.0) > BranchingValidator._TOLERANCE:
                raise BranchingConstraintError(
                    f"unit {uid}: sum of firing_prob = {total}, expected 1"
                )
