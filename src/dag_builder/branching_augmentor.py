import random
from typing import Dict, List, Set

import networkx as nx

from ..branching_validator import BranchingConstraintError, BranchingValidator
from ..common import Util
from ..config import Config
from ..exceptions import BuildFailedError


class BranchingAugmentor:
    """Insert cDAG / pDAG branching constructs into an existing DAG.

    Source nodes, sink nodes and chain heads (nodes with ``chain_id`` and no
    predecessor in their chain) are never replaced, so the entry/exit nodes and
    the release points of chains stay regular. Nodes created by a replacement
    inherit the ``chain_id`` of the replaced node. The branching parameters
    (p_b, d_b, the branch-count bounds, and the edge probability of gnp sub-DAGs)
    are drawn once per DAG; the retry count of the structural verification is
    stored in ``dag.graph["augmentation_retries"]``.
    """

    def __init__(self, config: Config, max_try: int = 100) -> None:
        self._config = config
        self._max_try = max_try
        self._next_node_id: int = 0
        self._next_unit_id: int = 0
        self._max_depth: int = 0
        self._p_b: float = 0.0
        self._min_branches: int = 2
        self._max_branches: int = 2
        self._edge_prob: float = 0.3

    def augment(self, dag: nx.DiGraph, layout_hint: str) -> nx.DiGraph:
        if layout_hint not in ("chain", "gnp", "fanin"):
            raise ValueError(f"unknown layout_hint: {layout_hint}")
        cfg = self._config
        self._max_depth = Util.random_choice(cfg.maximum_nesting_depth)
        self._p_b = Util.random_choice(cfg.probability_of_branching)
        self._min_branches = Util.random_choice(cfg.minimum_branches)
        self._max_branches = Util.random_choice(cfg.maximum_branches)
        # Fan-in/Fan-out hosts have no edge probability; 0.3 is the documented default.
        self._edge_prob = (Util.random_choice(cfg.probability_of_edge_existence)
                           if cfg.probability_of_edge_existence is not None else 0.3)
        protected = self._protected_nodes(dag)
        for try_i in range(1, self._max_try + 1):
            self._next_unit_id = 0
            work = dag.copy()
            self._next_node_id = max(work.nodes(), default=-1) + 1
            for n in work.nodes():
                work.nodes[n].setdefault("node_type", "regular")
            candidates = [n for n in nx.topological_sort(work)
                          if n not in protected and work.nodes[n]["node_type"] == "regular"]
            if layout_hint == "chain":
                self._augment_chain(work, 0, candidates)
            else:
                # The augmentation is orthogonal to the host construction method, so
                # Fan-in/Fan-out shares the gnp node-replacement strategy.
                self._augment_gnp(work, 0, candidates, initial_size=work.number_of_nodes())
            try:
                structure = BranchingValidator.assert_valid(work, cfg.firing)
            except BranchingConstraintError:
                if try_i == self._max_try:
                    raise BuildFailedError(
                        f"Branching augmentation failed after {self._max_try} tries"
                    )
                continue
            work.graph["augmentation_retries"] = try_i - 1
            if cfg.firing == "probabilistic":
                for n in work.nodes():
                    work.nodes[n]["marginal_prob"] = structure.marginal_prob(n)
            return work

    @staticmethod
    def _protected_nodes(dag: nx.DiGraph) -> Set[int]:
        protected = set(Util.get_source_nodes(dag)) | set(Util.get_sink_nodes(dag))
        for chain_nodes in Util.chains(dag).values():
            protected.add(Util.chain_head(dag, chain_nodes))
        return protected

    # ---------- chain mode ----------

    def _augment_chain(self, dag: nx.DiGraph, depth: int, candidates: List[int]) -> None:
        if depth >= self._max_depth:
            return
        new_subs: List[int] = []
        for v in candidates:
            if random.random() >= self._p_b:
                continue
            k = random.randint(self._min_branches, self._max_branches)
            if self._config.sub_chain_length is not None:
                length = Util.random_choice(self._config.sub_chain_length)
            else:
                length = max(1, len(nx.descendants(dag, v)))
            new_subs.extend(self._replace_node_with_branches(dag, v, k, length))
        if new_subs:
            self._augment_chain(dag, depth + 1, new_subs)

    def _replace_node_with_branches(self, dag: nx.DiGraph, v: int, k: int,
                                    length: int) -> List[int]:
        """Replace v with [v_ent, sub_seq_1..k, v_ext] in place.
        Returns the newly added regular sub-nodes (candidates at the next depth)."""
        inherited = self._inherited_attrs(dag, v)
        unit_id = self._take_unit_id()
        vent = self._add_node(dag, inherited, node_type="v_ent", branch_unit_id=unit_id,
                              execution_time=0)
        vext = self._add_node(dag, inherited, node_type="v_ext", branch_unit_id=unit_id,
                              execution_time=0)
        self._reconnect(dag, v, vent, vext)
        probs = self._sample_categorical(k)
        new_subs: List[int] = []
        for j in range(k):
            sub_nodes = [self._add_node(dag, inherited, node_type="regular", execution_time=0)
                         for _ in range(length)]
            new_subs.extend(sub_nodes)
            for a, b in zip(sub_nodes[:-1], sub_nodes[1:]):
                dag.add_edge(a, b)
            dag.add_edge(vent, sub_nodes[0], **self._branch_edge_attrs(j, probs))
            dag.add_edge(sub_nodes[-1], vext)
        return new_subs

    # ---------- gnp mode ----------

    def _augment_gnp(self, dag: nx.DiGraph, depth: int, candidates: List[int],
                     initial_size: int) -> None:
        if depth >= self._max_depth:
            return
        depth_remaining = self._max_depth - depth
        new_subs: List[int] = []
        for v in candidates:
            if random.random() >= self._p_b:
                continue
            k = random.randint(self._min_branches, self._max_branches)
            n_sub = max(2, initial_size // (k * (depth_remaining + 1)))
            new_subs.extend(self._replace_node_with_gnp_branches(dag, v, k, n_sub))
        if new_subs:
            self._augment_gnp(dag, depth + 1, new_subs, initial_size)

    def _replace_node_with_gnp_branches(self, dag: nx.DiGraph, v: int, k: int,
                                        n_sub: int) -> List[int]:
        """Replace v with [v_ent, sub_DAG_1..k via branch heads, v_ext] in place.
        Returns the newly added regular sub-nodes (branch heads + interior)."""
        inherited = self._inherited_attrs(dag, v)
        unit_id = self._take_unit_id()
        vent = self._add_node(dag, inherited, node_type="v_ent", branch_unit_id=unit_id,
                              execution_time=0)
        vext = self._add_node(dag, inherited, node_type="v_ext", branch_unit_id=unit_id,
                              execution_time=0)
        self._reconnect(dag, v, vent, vext)
        probs = self._sample_categorical(k)
        new_subs: List[int] = []
        for j in range(k):
            # A "branch head" receives the single v_ent -> head edge that carries
            # branch_id / firing_prob, and fans out to the sources of the G(n, p) body.
            head_id = self._add_node(dag, inherited, node_type="regular", execution_time=0)
            new_subs.append(head_id)
            sub_node_ids = [self._add_node(dag, inherited, node_type="regular", execution_time=0)
                            for _ in range(n_sub)]
            new_subs.extend(sub_node_ids)
            for ai in range(n_sub):
                for bi in range(ai + 1, n_sub):
                    if random.random() < self._edge_prob:
                        dag.add_edge(sub_node_ids[ai], sub_node_ids[bi])
            sub_subgraph = dag.subgraph(sub_node_ids)
            sources = [n for n in sub_node_ids if sub_subgraph.in_degree(n) == 0]
            sinks = [n for n in sub_node_ids if sub_subgraph.out_degree(n) == 0]
            dag.add_edge(vent, head_id, **self._branch_edge_attrs(j, probs))
            for src in sources:
                dag.add_edge(head_id, src)
            for sink in sinks:
                dag.add_edge(sink, vext)
        return new_subs

    # ---------- common ----------

    @staticmethod
    def _inherited_attrs(dag: nx.DiGraph, v: int) -> Dict[str, int]:
        return {k: dag.nodes[v][k] for k in ("chain_id",) if k in dag.nodes[v]}

    def _add_node(self, dag: nx.DiGraph, inherited: Dict[str, int], **attrs) -> int:
        n = self._take_node_id()
        dag.add_node(n, **inherited, **attrs)
        return n

    @staticmethod
    def _reconnect(dag: nx.DiGraph, v: int, vent: int, vext: int) -> None:
        """Move v's in-edges to v_ent and out-edges to v_ext (attributes preserved)."""
        in_edges = [(p, dict(dag.edges[p, v])) for p in dag.predecessors(v)]
        out_edges = [(s, dict(dag.edges[v, s])) for s in dag.successors(v)]
        dag.remove_node(v)
        for p, attrs in in_edges:
            dag.add_edge(p, vent, **attrs)
        for s, attrs in out_edges:
            dag.add_edge(vext, s, **attrs)

    def _branch_edge_attrs(self, j: int, probs: List[float]) -> Dict[str, float]:
        attrs: Dict[str, float] = {"branch_id": j}
        if self._config.firing == "probabilistic":
            attrs["firing_prob"] = float(probs[j])
        return attrs

    def _take_node_id(self) -> int:
        n = self._next_node_id
        self._next_node_id += 1
        return n

    def _take_unit_id(self) -> int:
        u = self._next_unit_id
        self._next_unit_id += 1
        return u

    def _sample_categorical(self, k: int) -> List[float]:
        """Draw F(theta_x) from the single seeded ``random`` generator.

        ``dirichlet`` normalises Gamma(alpha, 1) draws (uniform on the simplex for
        alpha = 1); ``uniform-normalize`` normalises U(0, 1) draws as in Zhao 2025.
        """
        dist = self._config.probability_distribution
        if dist == "dirichlet":
            alpha = float(self._config.dirichlet_alpha)
            r = [random.gammavariate(alpha, 1.0) for _ in range(k)]
        elif dist == "uniform-normalize":
            r = [random.uniform(0.0, 1.0) for _ in range(k)]
        else:
            raise ValueError(f"unknown distribution: {dist}")
        s = sum(r)
        return [x / s for x in r] if s > 0 else [1.0 / k] * k
