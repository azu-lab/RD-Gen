import random
from typing import List

import networkx as nx
import numpy as np

from ..branching_validator import BranchingConstraintError, BranchingValidator
from ..common import Util
from ..config import Config
from ..exceptions import BuildFailedError


class BranchingAugmentor:
    """Insert cDAG / pDAG branching constructs into an existing DAG."""

    def __init__(self, config: Config, max_try: int = 100) -> None:
        self._config = config
        self._max_try = max_try
        self._next_node_id: int = 0
        self._next_unit_id: int = 0

    def augment(self, dag: nx.DiGraph, layout_hint: str) -> nx.DiGraph:
        for try_i in range(1, self._max_try + 1):
            self._next_unit_id = 0
            work = dag.copy()
            self._next_node_id = max(work.nodes(), default=-1) + 1
            for n in list(work.nodes()):
                work.nodes[n].setdefault("node_type", "regular")
            if layout_hint == "chain":
                result = self._augment_chain(work, current_depth=0)
            elif layout_hint in ("gnp", "fanin"):
                # Per the "1 logical node" framing in the paper, the augmentation
                # is orthogonal to the host construction method, so Fan-in/Fan-out
                # shares the gnp node-replacement strategy.
                result = self._augment_gnp(work, current_depth=0,
                                           initial_size=work.number_of_nodes())
            else:
                raise ValueError(f"unknown layout_hint: {layout_hint}")
            try:
                BranchingValidator.assert_valid(result, self._config.firing)
                return result
            except BranchingConstraintError:
                if try_i == self._max_try:
                    raise BuildFailedError(
                        f"Branching augmentation failed after {self._max_try} tries"
                    )
                continue

    # ---------- chain mode ----------

    def _augment_chain(self, dag: nx.DiGraph, current_depth: int,
                       candidate_filter=None) -> nx.DiGraph:
        max_depth = Util.random_choice(self._config.maximum_nesting_depth)
        if current_depth >= max_depth:
            return dag
        p_b = Util.random_choice(self._config.probability_of_branching)
        max_branches = Util.random_choice(self._config.maximum_branches)

        topo = list(nx.topological_sort(dag))
        if candidate_filter is not None:
            candidates = [n for n in topo
                          if n in candidate_filter
                          and dag.nodes[n].get("node_type") == "regular"]
        else:
            candidates = [n for n in topo
                          if dag.nodes[n].get("node_type") == "regular"]

        newly_added_at_next_depth = []
        for v in candidates:
            if v not in dag.nodes():
                continue
            if random.random() >= p_b:
                continue
            k = random.randint(2, max(2, max_branches))
            remaining = self._chain_position_remaining(dag, v)
            L_sub = max(1, remaining)
            new_subs = self._replace_node_with_branches(dag, v, k, L_sub)
            newly_added_at_next_depth.extend(new_subs)

        if newly_added_at_next_depth:
            self._augment_chain(dag, current_depth + 1,
                                 candidate_filter=set(newly_added_at_next_depth))
        return dag

    def _chain_position_remaining(self, dag: nx.DiGraph, v: int) -> int:
        """Approximate remaining chain length at v, used as subsequence length."""
        try:
            descendants = nx.descendants(dag, v)
            return max(1, len(descendants))
        except nx.NetworkXError:
            return 1

    def _replace_node_with_branches(self, dag: nx.DiGraph, v: int, k: int,
                                    L_sub: int) -> list:
        """Replace v with [v_ent, sub_seq_1..k, v_ext] in place.
        Returns the list of newly added regular sub-nodes (for next-depth processing)."""
        unit_id = self._take_unit_id()
        vent = self._take_node_id()
        vext = self._take_node_id()
        dag.add_node(vent, node_type="v_ent", branch_unit_id=unit_id, execution_time=0)
        dag.add_node(vext, node_type="v_ext", branch_unit_id=unit_id, execution_time=0)
        in_edges = [(p, dict(dag.edges[p, v])) for p in dag.predecessors(v)]
        succs = list(dag.successors(v))
        dag.remove_node(v)
        for p, edge_attrs in in_edges:
            dag.add_edge(p, vent, **edge_attrs)
        for s in succs:
            dag.add_edge(vext, s)
        probs = self._sample_categorical(k)
        new_subs = []
        for j in range(k):
            sub_nodes = [self._take_node_id() for _ in range(L_sub)]
            for n in sub_nodes:
                dag.add_node(n, node_type="regular", execution_time=0)
                new_subs.append(n)
            for a, b in zip(sub_nodes[:-1], sub_nodes[1:]):
                dag.add_edge(a, b)
            attrs = {"branch_id": j}
            if self._config.firing == "probabilistic":
                attrs["firing_prob"] = float(probs[j])
            dag.add_edge(vent, sub_nodes[0], **attrs)
            dag.add_edge(sub_nodes[-1], vext)
        return new_subs

    # ---------- gnp mode (Task 4) ----------

    def _augment_gnp(self, dag: nx.DiGraph, current_depth: int,
                     initial_size: int, candidate_filter=None) -> nx.DiGraph:
        max_depth = Util.random_choice(self._config.maximum_nesting_depth)
        if current_depth >= max_depth:
            return dag
        p_b = Util.random_choice(self._config.probability_of_branching)
        max_branches = Util.random_choice(self._config.maximum_branches)
        depth_remaining = max(0, max_depth - current_depth)

        topo = list(nx.topological_sort(dag))
        if candidate_filter is not None:
            candidates = [n for n in topo
                          if n in candidate_filter
                          and dag.nodes[n].get("node_type") == "regular"]
        else:
            candidates = [n for n in topo
                          if dag.nodes[n].get("node_type") == "regular"]

        newly_added_at_next_depth = []
        for v in candidates:
            if v not in dag.nodes():
                continue
            if random.random() >= p_b:
                continue
            k = random.randint(2, max(2, max_branches))
            n_sub = max(2, initial_size // max(1, k * (depth_remaining + 1)))
            new_subs = self._replace_node_with_gnp_branches(dag, v, k, n_sub)
            newly_added_at_next_depth.extend(new_subs)

        if newly_added_at_next_depth:
            self._augment_gnp(dag, current_depth + 1, initial_size,
                               candidate_filter=set(newly_added_at_next_depth))
        return dag

    def _replace_node_with_gnp_branches(self, dag: nx.DiGraph, v: int, k: int,
                                         n_sub: int) -> list:
        """Replace v with [v_ent, sub_DAG_1..k via branch heads, v_ext] in place.
        Returns the list of newly added regular sub-nodes (branch heads + interior)."""
        unit_id = self._take_unit_id()
        vent = self._take_node_id()
        vext = self._take_node_id()
        dag.add_node(vent, node_type="v_ent", branch_unit_id=unit_id, execution_time=0)
        dag.add_node(vext, node_type="v_ext", branch_unit_id=unit_id, execution_time=0)
        # Preserve in-edge / out-edge attributes
        in_edges = [(p, dict(dag.edges[p, v])) for p in dag.predecessors(v)]
        out_edges = [(s, dict(dag.edges[v, s])) for s in dag.successors(v)]
        dag.remove_node(v)
        for p, attrs in in_edges:
            dag.add_edge(p, vent, **attrs)
        for s, attrs in out_edges:
            dag.add_edge(vext, s, **attrs)

        probs = self._sample_categorical(k)
        edge_prob = (Util.random_choice(self._config.probability_of_edge_existence)
                     if self._config.probability_of_edge_existence is not None
                     else 0.3)

        new_subs = []
        for j in range(k):
            # Each branch gets its own internal Erdős-Rényi mini-DAG of n_sub nodes,
            # plus a "branch head" node that receives the v_ent -> head edge with
            # branch_id/firing_prob attributes (single edge from v_ent per branch,
            # required for clean branch_id semantics).
            head_id = self._take_node_id()
            dag.add_node(head_id, node_type="regular", execution_time=0)
            new_subs.append(head_id)

            sub_node_ids = [self._take_node_id() for _ in range(n_sub)]
            for n in sub_node_ids:
                dag.add_node(n, node_type="regular", execution_time=0)
                new_subs.append(n)
            for ai in range(n_sub):
                for bi in range(ai + 1, n_sub):
                    if random.random() < edge_prob:
                        dag.add_edge(sub_node_ids[ai], sub_node_ids[bi])

            sub_subgraph = dag.subgraph(sub_node_ids)
            sources = [n for n in sub_node_ids if sub_subgraph.in_degree(n) == 0]
            sinks = [n for n in sub_node_ids if sub_subgraph.out_degree(n) == 0]
            if not sources:
                sources = [sub_node_ids[0]]
            if not sinks:
                sinks = [sub_node_ids[-1]]

            attrs = {"branch_id": j}
            if self._config.firing == "probabilistic":
                attrs["firing_prob"] = float(probs[j])
            dag.add_edge(vent, head_id, **attrs)
            for src in sources:
                dag.add_edge(head_id, src)
            for sink in sinks:
                dag.add_edge(sink, vext)
        return new_subs

    # ---------- common ----------

    def _take_node_id(self) -> int:
        n = self._next_node_id
        self._next_node_id += 1
        return n

    def _take_unit_id(self) -> int:
        u = self._next_unit_id
        self._next_unit_id += 1
        return u

    def _sample_categorical(self, k: int) -> List[float]:
        dist = self._config.probability_distribution
        if dist == "dirichlet":
            alpha = float(self._config.dirichlet_alpha)
            return list(np.random.dirichlet([alpha] * k))
        elif dist == "uniform-normalize":
            r = [random.uniform(0.0, 1.0) for _ in range(k)]
            s = sum(r)
            return [x / s for x in r]
        else:
            raise ValueError(f"unknown distribution: {dist}")
