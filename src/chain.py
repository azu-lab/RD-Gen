import networkx as nx
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
            G.add_node(G.number_of_nodes(), execution_time=random_get_exec_time(conf))
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


def _vertically_link_chains(conf, chains: List[Chain], G: nx.DiGraph) -> None:
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


def _merge_chains(conf, chains: List[int], G: nx.DiGraph) -> None:
    # Number of exit nodes がある場合、これも考慮
    pass # TODO
