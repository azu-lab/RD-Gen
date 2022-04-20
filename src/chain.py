import networkx as nx
import numpy as np
import random
import copy
import itertools
from typing import List

from utils import random_get_exec_time


class Chain:
    def __init__(self, nodes: List[int], head: int, tails: List[int]) -> None:
        self.nodes = nodes
        self.head = head
        self.tails = tails
        self.unlinked_tails = tails
        self.level = -1

    def get_sum_cost(self, conf, G: nx.DiGraph) -> int:
        sum_cost = 0
        if('Use communication time' in conf.keys()):
            edges_in_chain = set()
            for node_i in self.nodes:
                sum_cost += G.nodes[node_i]['exec']
                edges_in_chain |= {(s, t) for s, t in G.out_edges(node_i) if t in self.nodes}
            for s, t in edges_in_chain:
                sum_cost += G.edges[s, t]['comm']
        else:
            for node_i in self.nodes:
                sum_cost += G.nodes[node_i]['exec']

        return sum_cost

    def get_edges(self, G: nx.DiGraph) -> List[int]:
        edges_in_chain = set()
        for node_i in self.nodes:
            edges_in_chain |= {(s, t) for s, t in G.out_edges(node_i) if t in self.nodes}

        return list(edges_in_chain)


def _create_chain(conf, num_nodes: int, G: nx.DiGraph) -> Chain:
    # Determine the number of nodes in each sub chain  # HACK
    first_sub_len = random.randint(conf['Chain length']['Min'], conf['Chain length']['Max'])
    sub_len_options = list(range(1, conf['Chain length']['Max']+1))
    sub_len_combos = []
    while(not sub_len_combos):
        first_sub_len = random.randint(conf['Chain length']['Min'], conf['Chain length']['Max'])
        remain_num_nodes = num_nodes - first_sub_len
        chain_width = random.randint(conf['Chain width']['Min']-1, conf['Chain width']['Max']-1)
        for sub_len_combo in itertools.combinations_with_replacement(sub_len_options, chain_width):
            if(sum(sub_len_combo) == remain_num_nodes and
                    len([i for i, v in enumerate(sub_len_combo) if v == conf['Chain length']['Max']]) <= 1):
                sub_len_combos.append(sub_len_combo)
    sub_chain_len_combo = list(random.choice(sub_len_combos)) + [first_sub_len]

    # Generate sub chains
    sub_chain_dict = {str(sub_chain_i):[] for sub_chain_i in range(len(sub_chain_len_combo))}
    for sub_chain_i, sub_chain_len in enumerate(sub_chain_len_combo):
        for _ in range(sub_chain_len):
            sub_chain_dict[str(sub_chain_i)].append(G.number_of_nodes())
            G.add_node(G.number_of_nodes(), exec=random_get_exec_time(conf))
            if(len(sub_chain_dict[str(sub_chain_i)]) >= 2):
                G.add_edge(sub_chain_dict[str(sub_chain_i)][-2], sub_chain_dict[str(sub_chain_i)][-1])
    
    # Merge into the longest subchain
    longest_subchain_i = sub_chain_len_combo.index(max(sub_chain_len_combo))
    longest_sub_chain = sub_chain_dict[str(longest_subchain_i)]
    chain = copy.deepcopy(sub_chain_dict[str(longest_subchain_i)])
    for sub_chain_i, nodes in sub_chain_dict.items():
        if(sub_chain_i == str(longest_subchain_i)):
            continue
        if(conf['Chain length']['Max'] - len(nodes) == 1):
            source_i = longest_sub_chain[0]
        else:
            source_i = random.choice(longest_sub_chain[0:(conf['Chain length']['Max']-len(nodes)+1)])
        G.add_edge(source_i, nodes[0])
        chain += nodes

    # Create chain
    head = None
    tails = []
    for node_i in chain:
        if(G.in_degree(node_i) == 0):
            head = node_i
        if(G.out_degree(node_i) == 0):
            tails.append(node_i)

    return Chain(chain, head, tails)


def vertically_link_chains(conf, chains: List[Chain], G: nx.DiGraph) -> None:
    source_chains = random.sample(chains, conf['Vertically link chains']['Number of entry nodes'])
    for source_chain in source_chains:
        source_chain.level = 1
    target_chains = [c for c in chains if c.level == -1]
    while(target_chains):
        source_chain = random.choice(source_chains)
        source_tail = random.choice(source_chain.unlinked_tails)
        target_chain = random.choice(target_chains)
        
        G.add_edge(source_tail, target_chain.head)
        target_chain.level = source_chain.level + 1
        target_chains.remove(target_chain)
        if('Max level of vertical links' in conf['Vertically link chains'] and
                target_chain.level != conf['Vertically link chains']['Max level of vertical links']):
            source_chains.append(target_chain)
        source_chain.unlinked_tails.remove(source_tail)
        if(not source_chain.unlinked_tails):
            source_chains.remove(source_chain)


def merge_chains(conf, chains: List[Chain], G: nx.DiGraph) -> None:
    # Determine source tails
    exit_options = []
    for chain in chains:
        exit_options += chain.unlinked_tails
    exit_nodes = random.sample(exit_options, conf['Merge chains']['Number of exit nodes'])
    source_tails = list(set(exit_options) - set(exit_nodes))

    # Determine target nodes
    target_nodes = set()
    true_keys = [k for k, v in conf['Merge chains'].items() if v==True]
    if('Head of chain' in true_keys):
        target_nodes |= {c.head for c in chains} - {v for v, d in G.in_degree() if d == 0}
    if('Exit node' in true_keys):
        target_nodes |= set(exit_nodes)
    if('Middle of chain' in true_keys):
        for chain in chains:
            nodes_except_head = copy.deepcopy(chain.nodes)
            nodes_except_head.remove(chain.head)
            target_nodes |= set(nodes_except_head) - set(chain.tails)

    # Merge
    while(source_tails):
        source_tail = random.choice(source_tails)
        target_node = random.choice(list(target_nodes - set(nx.ancestors(G, source_tail))))
        G.add_edge(source_tail, target_node)
        source_tails.remove(source_tail)
