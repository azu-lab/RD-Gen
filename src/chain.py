import networkx as nx
import numpy as np
import random
import copy
import itertools
from typing import List

from src.utils import choice_one_from_cfg, get_max_of_range, get_min_of_range
from src.abbreviation import ToO


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


def generate_chain(cfg, num_nodes: int, G: nx.DiGraph) -> Chain:
    ### Determine chain width
    if('Fixed' in cfg['Chain width'].keys()):
        chain_width = cfg['Chain width']['Fixed']
    elif('Random' in cfg['Chain width'].keys()):
        lower_bound = int(np.ceil(num_nodes / get_max_of_range(cfg[ToO['CL']])))
        upper_bound = int(np.floor(num_nodes / get_min_of_range(cfg[ToO['CL']])))
        choices = [v for v in cfg['Chain width']['Random'] if lower_bound <= v <= upper_bound]
        chain_width = random.choice(choices)

    ### Determine the length of main sequence
    if('Fixed' in cfg['Chain length'].keys()):
        main_len = cfg['Chain length']['Fixed']
    elif('Random' in cfg['Chain length'].keys()):
        lower_bound = int(np.ceil(num_nodes / chain_width))
        upper_bound = int(np.floor(num_nodes - chain_width + 1))
        choices = [v for v in cfg['Chain length']['Random'] if lower_bound <= v <= upper_bound]
        main_len = random.choice(choices)

    ### Determine the length of each sub sequence
    remain_num_nodes = num_nodes - main_len
    choices_sub_len = list(range(1, main_len+1))
    combos_sub_len = []
    for combo in itertools.combinations_with_replacement(choices_sub_len, chain_width):
        if(sum(combo) == remain_num_nodes):
            combos_sub_len.append(combo)

    sequence_len_list = list(random.choice(combos_sub_len)) + [main_len]

    ### Generate sub chains
    sub_chain_dict = {str(sub_chain_i):[] for sub_chain_i in range(len(sub_chain_len_combo))}
    for sub_chain_i, sub_chain_len in enumerate(sub_chain_len_combo):
        for _ in range(sub_chain_len):
            sub_chain_dict[str(sub_chain_i)].append(G.number_of_nodes())
            G.add_node(G.number_of_nodes(), exec=random_get_exec(cfg))
            if(len(sub_chain_dict[str(sub_chain_i)]) >= 2):
                G.add_edge(sub_chain_dict[str(sub_chain_i)][-2], sub_chain_dict[str(sub_chain_i)][-1])
    
    # Merge into the longest subchain
    longest_subchain_i = sub_chain_len_combo.index(max(sub_chain_len_combo))
    longest_sub_chain = sub_chain_dict[str(longest_subchain_i)]
    chain = copy.deepcopy(sub_chain_dict[str(longest_subchain_i)])
    for sub_chain_i, nodes in sub_chain_dict.items():
        if(sub_chain_i == str(longest_subchain_i)):
            continue
        if(cfg['Chain length']['Max'] - len(nodes) == 1):
            source_i = longest_sub_chain[0]
        else:
            source_i = random.choice(longest_sub_chain[0:(cfg['Chain length']['Max']-len(nodes)+1)])
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


# def vertically_link_chains(conf, chains: List[Chain], G: nx.DiGraph) -> None:
#     source_chains = random.sample(chains, conf['Vertically link chains']['Number of entry nodes'])
#     for source_chain in source_chains:
#         source_chain.level = 1
#     target_chains = [c for c in chains if c.level == -1]
#     while(target_chains):
#         source_chain = random.choice(source_chains)
#         source_tail = random.choice(source_chain.unlinked_tails)
#         target_chain = random.choice(target_chains)
        
#         G.add_edge(source_tail, target_chain.head)
#         target_chain.level = source_chain.level + 1
#         target_chains.remove(target_chain)
#         if('Max level of vertical links' in conf['Vertically link chains'] and
#                 target_chain.level != conf['Vertically link chains']['Max level of vertical links']):
#             source_chains.append(target_chain)
#         source_chain.unlinked_tails.remove(source_tail)
#         if(not source_chain.unlinked_tails):
#             source_chains.remove(source_chain)


# def merge_chains(conf, chains: List[Chain], G: nx.DiGraph) -> None:
#     # Determine source tails
#     exit_options = []
#     for chain in chains:
#         exit_options += chain.unlinked_tails
#     exit_nodes = random.sample(exit_options, conf['Merge chains']['Number of exit nodes'])
#     source_tails = list(set(exit_options) - set(exit_nodes))

#     # Determine target nodes
#     target_nodes = set()
#     true_keys = [k for k, v in conf['Merge chains'].items() if v==True]
#     if('Head of chain' in true_keys):
#         target_nodes |= {c.head for c in chains} - {v for v, d in G.in_degree() if d == 0}
#     if('Exit node' in true_keys):
#         target_nodes |= set(exit_nodes)
#     if('Middle of chain' in true_keys):
#         for chain in chains:
#             nodes_except_head = copy.deepcopy(chain.nodes)
#             nodes_except_head.remove(chain.head)
#             target_nodes |= set(nodes_except_head) - set(chain.tails)

#     # Merge
#     while(source_tails):
#         source_tail = random.choice(source_tails)
#         target_node = random.choice(list(target_nodes - set(nx.ancestors(G, source_tail))))
#         G.add_edge(source_tail, target_node)
#         source_tails.remove(source_tail)
