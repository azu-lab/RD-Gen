import networkx as nx
import numpy as np
import random
import copy
import itertools
from typing import List, Tuple

from src.utils import choice_one_from_cfg, get_max_of_range, get_min_of_range, get_cp
from src.random_set_exec import random_get_exec
from src.abbreviation import TO_ORI
from src.exceptions import NoSettablePeriodError


class Chain:
    def __init__(self, nodes: List[int], head: int, tails: List[int]) -> None:
        self.nodes = nodes
        self.head = head
        self.tails = copy.deepcopy(tails)
        self.unlinked_tails = copy.deepcopy(tails)
        self.level = -1

    def _get_cp(self, dag: nx.DiGraph) -> Tuple[List[int], int]:
        cp = None
        cp_len = 0
        for tail in self.tails:
            path, path_len = get_cp(dag, self.head, tail)
            if(path_len > cp_len):
                cp = path
                cp_len = path_len

        return cp, cp_len

    def random_set_exec(self, cfg, G: nx.DiGraph) -> None:
        if(TO_ORI['UMP'] in cfg.keys()
           and cfg[TO_ORI['UMP']][TO_ORI['PT']] == 'Chain'):
            upper_bound_cp_len = int(np.floor((G.nodes[self.head]['period']
                                               * choice_one_from_cfg(cfg[TO_ORI['UMP']][TO_ORI['MREP']]))))

            # Determine the maximum execution time of a single node on longest path
            max_hop = 0
            for tail in self.tails:
                if(self.head == tail):
                    if(1 > max_hop):
                        max_hop = 1
                else:
                    paths = nx.all_simple_paths(
                        G, source=self.head, target=tail)
                    if((hop := max([len(p) for p in paths])) > max_hop):
                        max_hop = hop
            max_exec = int(upper_bound_cp_len / max_hop)

            # Random set (temp)
            if('Fixed' in cfg['Execution time'].keys()):
                choices = [cfg['Execution time']['Fixed']]
            elif('Random' in cfg['Execution time'].keys()):
                choices = [v for v in cfg['Execution time']
                           ['Random'] if v <= max_exec]
            for node_i in self.nodes:
                G.nodes[node_i]['exec'] = random.choice(choices)

            # Adjustment not to exceed the upper bound
            continue_flag = True
            while(continue_flag):
                cp, cp_len = self._get_cp(G)
                if(cp_len > upper_bound_cp_len):
                    decrease_flag = False
                    random.shuffle(cp)
                    for node_i in cp:
                        if(G.nodes[node_i]['exec'] > get_min_of_range(cfg[TO_ORI['ET']])):
                            G.nodes[node_i]['exec'] -= 1
                            decrease_flag = True
                            break
                    if(not decrease_flag):
                        upper_bound_period = get_max_of_range(
                            cfg[TO_ORI['UMP']][TO_ORI['P']])
                        if(G.nodes[self.head]['period'] == upper_bound_period):
                            raise NoSettablePeriodError
                        else:
                            # HACK
                            G.nodes[self.head]['period'] = upper_bound_period
                else:
                    continue_flag = False

        else:
            for node_i in self.nodes:
                G.nodes[node_i]['exec'] = random_get_exec(cfg, G, node_i)


def generate_single_chain(cfg, num_nodes: int, G: nx.DiGraph) -> Chain:
    # Determine chain width
    if('Fixed' in cfg['Chain width'].keys()):
        chain_width = cfg['Chain width']['Fixed']
    elif('Random' in cfg['Chain width'].keys()):
        lower_bound = int(
            np.ceil(num_nodes / get_max_of_range(cfg[TO_ORI['CL']])))
        upper_bound = int(
            np.floor(num_nodes / get_min_of_range(cfg[TO_ORI['CL']])))
        choices = [v for v in cfg['Chain width']
                   ['Random'] if lower_bound <= v <= upper_bound]
        chain_width = random.choice(choices)

    # Determine the length of main sequence
    if('Fixed' in cfg['Chain length'].keys()):
        main_len = cfg['Chain length']['Fixed']
    elif('Random' in cfg['Chain length'].keys()):
        lower_bound = int(np.ceil(num_nodes / chain_width))
        upper_bound = int(np.floor(num_nodes - chain_width + 1))
        choices = [v for v in cfg['Chain length']
                   ['Random'] if lower_bound <= v <= upper_bound]
        main_len = random.choice(choices)

    # Create length list of each sequence
    if(chain_width == 1):
        sequence_len_list = [main_len]
    else:
        # Determine the length of each sub sequence
        remain_num_nodes = num_nodes - main_len
        choices_sub_len = list(range(1, main_len+1))
        combos_sub_len = []
        for combo in itertools.combinations_with_replacement(choices_sub_len, chain_width-1):
            if(sum(combo) == remain_num_nodes):
                combos_sub_len.append(combo)

        sequence_len_list = list(random.choice(combos_sub_len)) + [main_len]

    # Generate sequences
    sequences_dict = {str(seq_i): []
                      for seq_i in range(len(sequence_len_list))}
    for seq_i, seq_len in enumerate(sequence_len_list):
        for _ in range(seq_len):
            sequences_dict[str(seq_i)].append(G.number_of_nodes())
            G.add_node(G.number_of_nodes())
            if(len(sequences_dict[str(seq_i)]) >= 2):
                G.add_edge(sequences_dict[str(seq_i)]
                           [-2], sequences_dict[str(seq_i)][-1])

    if(chain_width == 1):
        chain = sequences_dict[str(0)]
    else:
        # Merge the sub sequences into the main sequence
        main_seq_i = sequence_len_list.index(max(sequence_len_list))
        main_seq = sequences_dict[str(main_seq_i)]
        chain = copy.deepcopy(main_seq)
        for seq_i, nodes in sequences_dict.items():
            if(seq_i == str(main_seq_i)):
                continue
            if(get_max_of_range(cfg[TO_ORI['CL']]) - len(nodes) == 1):
                source_i = main_seq[0]
            else:
                source_i = random.choice(
                    main_seq[0: (get_max_of_range(cfg[TO_ORI['CL']])-len(nodes)+1)])
            G.add_edge(source_i, nodes[0])
            chain += nodes

    # Generate chain
    head = None
    tails = []
    for node_i in chain:
        if(G.in_degree(node_i) == 0):
            head = node_i
        if(G.out_degree(node_i) == 0):
            tails.append(node_i)

    return Chain(chain, head, tails)


def vertically_link_chains(cfg, chains: List[Chain], G: nx.DiGraph) -> None:
    source_chains = random.sample(chains,
                                  choice_one_from_cfg(cfg[TO_ORI['VLC']][TO_ORI['NEN']]))
    for source_chain in source_chains:
        source_chain.level = 1
    target_chains = [c for c in chains if c.level == -1]
    while(target_chains):
        source_chain = random.choice(source_chains)
        source_tail = random.choice(source_chain.unlinked_tails)
        target_chain = random.choice(target_chains)

        G.add_edge(source_tail,
                   target_chain.head,
                   comm=choice_one_from_cfg(cfg[TO_ORI['UCT']]))
        target_chain.level = source_chain.level + 1
        target_chains.remove(target_chain)
        if(TO_ORI['MLV'] in cfg[TO_ORI['VLC']]
                and target_chain.level != get_max_of_range(cfg[TO_ORI['VLC']][TO_ORI['MLV']])):
            source_chains.append(target_chain)
        source_chain.unlinked_tails.remove(source_tail)
        if(not source_chain.unlinked_tails):
            source_chains.remove(source_chain)


def merge_chains(cfg, chains: List[Chain], G: nx.DiGraph) -> None:
    # Determine source tails
    exit_choices = []
    for chain in chains:
        exit_choices += chain.unlinked_tails
    exit_nodes = random.sample(exit_choices,
                               choice_one_from_cfg(cfg[TO_ORI['MGC']][TO_ORI['NEX']]))
    source_tails = list(set(exit_choices) - set(exit_nodes))

    # Determine target nodes
    target_nodes = set()
    true_keys = [k for k, v in cfg[TO_ORI['MGC']].items() if v == True]
    if('Head of chain' in true_keys):
        target_nodes |= {c.head for c in chains} - \
            {v for v, d in G.in_degree() if d == 0}
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
        target_node = random.choice(
            list(target_nodes - set(nx.ancestors(G, source_tail))))
        G.add_edge(source_tail,
                   target_node,
                   comm=choice_one_from_cfg(cfg[TO_ORI['UCT']]))
        source_tails.remove(source_tail)
