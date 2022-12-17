
import copy
import random
from typing import Dict, Generator, List
from tqdm import tqdm

import networkx as nx
from src.builder.dag_builder_base import DAGBuilderBase
from src.config import Config


class Chain(DAGBuilderBase):
    node_i = 0

    def __init__(
            self,
            cfg: Config
    ) -> None:
        super().__init__(cfg)
        self._G = nx.DiGraph()
        self._head = Chain.node_i
        self._main_tail: List[int] = []
        self._sub_tails: List[int] = []

    def _add_node(
        self
    ) -> int:
        self._G.add_node(Chain.node_i)
        Chain.node_i += 1

        return self.node_i - 1

    def _get_sub_seq_len_upper(
        self,
        src_i: int
    ) -> int:
        main_tail_i = [v for v, d in self._G.out_degree() if d == 0]
        return (
            len(list(nx.all_simple_paths(
                self._G,
                source=src_i,
                target=main_tail_i))[0]) - 1
        )

    def has_tail(
        self
    ) -> bool:
        tails = []
        if self._cfg.get_value(["GS", "VLC", "MST"]):
            tails += self._main_tail
        if self._cfg.get_value(["GS", "VLC", "SST"]):
            tails += self._sub_tails

        if tails:
            return True
        else:
            return False

    def random_choice_src_tail(
        self
    ) -> int:
        tails = []
        if self._cfg.get_value(["GS", "VLC", "MST"]):
            tails += self._main_tail
        if self._cfg.get_value(["GS", "VLC", "SST"]):
            tails += self._sub_tails

        choose_tail = random.choice(tails)
        if choose_tail in self._main_tail:
            self._main_tail.remove(choose_tail)
        else:
            self._sub_tails.remove(choose_tail)

        return choose_tail

    def build(
        self
    ) -> None:
        # Build main sequence
        main_len = self.random_choice(self._cfg.get_value(["GS", "MSL"]))
        for i in range(main_len):
            add_node_i = self._add_node()
            if self._G.number_of_nodes() > 1:
                self._G.add_edge(add_node_i-1, add_node_i)
            if i == main_len-1:
                self._main_tail.append(add_node_i)

        # Build sub sequence (Optional)
        if num_sub_sequences := self._cfg.get_value(["GS", "NSS"]):
            sub_sequences: List[Dict] = []
            for _ in range(self.random_choice(num_sub_sequences)):
                sub_seq = {"src_i": self.random_choice(
                    list(self._G.nodes())[:-1])}
                sub_seq["len"] = random.randint(
                    1, self._get_sub_seq_len_upper(sub_seq["src_i"]))
                sub_sequences.append(sub_seq)

            for sub_seq in sub_sequences:
                for i in range(sub_seq["len"]):
                    if i == 0:
                        add_node_i = self._add_node()
                        self._G.add_edge(sub_seq["src_i"], add_node_i)
                    else:
                        add_node_i = self._add_node()
                        self._G.add_edge(add_node_i-1, add_node_i)
                        if i == sub_seq["len"]-1:
                            self._sub_tails.append(add_node_i)


chains: List[Chain] = []


class ChainBasedBuilder(DAGBuilderBase):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        super().__init__(cfg)

    def build(self) -> Generator[nx.DiGraph, None, None]:
        for _ in tqdm(range(self._cfg.get_value(["NG"]))):
            # Build each chain
            global chains
            chains = []
            num_chain_choices = self._cfg.get_value(["GS", "NC"])
            for _ in range(self.random_choice(num_chain_choices)):
                chain = Chain(self._cfg)
                chain.build()
                chains.append(chain)
            Chain.node_i = 0

            # Union chains
            chain_dags = [copy.deepcopy(c._G) for c in chains]
            G = nx.disjoint_union_all(chain_dags)

            # Vertically link chains
            if self._cfg.get_param(["GS", "VLC"]):
                # Initialize variables
                num_entry = self.random_choice(
                    self._cfg.get_value(["GS", "VLC", "NEN"]))
                tgt_chain_choice = copy.deepcopy(chains)
                random.shuffle(tgt_chain_choice)
                src_chains = [tgt_chain_choice.pop(
                    0) for _ in range(num_entry)]

                while src_chain_choice := [c for c in src_chains if c.has_tail()]:
                    # Determine source tail
                    src_chain = random.choice(src_chain_choice)
                    src_tail_i = src_chain.random_choice_src_tail()

                    # Determine target chain
                    random.shuffle(tgt_chain_choice)
                    num_tgt_chains = random.randint(1, 3)
                    tgt_chains: List[Chain] = []
                    for chain in tgt_chain_choice:
                        if chain._head > src_tail_i:
                            tgt_chains.append(chain)
                            if len(tgt_chains) == num_tgt_chains:
                                break

                    # Add edge
                    if tgt_chains:
                        for tgt_chain in tgt_chains:
                            G.add_edge(src_tail_i, tgt_chain._head)
                            src_chains.append(tgt_chain)

            # Merge chains
            if self._cfg.get_param(["GS", "MGC"]):
                # Initialize variables
                src_tails = [v for v, d in G.out_degree() if d == 0]
                num_exit = self.random_choice(
                    self._cfg.get_value(["GS", "MGC", "NEX"]))
                while num_exit > len(src_tails):  # HACK
                    num_exit = self.random_choice(
                        self._cfg.get_value(["GS", "MGC", "NEX"]))
                random.shuffle(src_tails)
                exit_nodes = {src_tails.pop(0) for _ in range(num_exit)}

                tgt_nodes = set()
                if self._cfg.get_value(["GS", "MGC", "MDC"]):
                    tgt_nodes |= set(G.nodes()) - exit_nodes
                if self._cfg.get_value(["GS", "MGC", "EXN"]):
                    tgt_nodes |= exit_nodes
                for src_tail_i in src_tails:
                    tgt_node_i = random.choice(
                        list(tgt_nodes - set(nx.ancestors(G, src_tail_i))))
                    G.add_edge(src_tail_i, tgt_node_i)

            yield G
