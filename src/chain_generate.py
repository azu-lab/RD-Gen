import numpy as np
import networkx as nx
import random
import copy
import itertools
from typing import List, Tuple

from utils import option_parser, set_end_to_end_deadlines, random_get_comm_time, random_get_exec_time
from file_handling_helper import load_chain_config
from write_dag import write_dag
from random_set_period import random_set_period


def _generate_chain(conf, num_nodes: int, G: nx.DiGraph) -> List[int]:
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

    return chain


def main(conf, dest_dir):
    for dag_i in range(conf['Number of DAGs']):
        random.seed(conf['Initial seed'] + dag_i)
        G = nx.DiGraph()

        # Determine the number of nodes in each chain
        min_nodes = conf['Chain length']['Min'] + conf['Chain width']['Min'] - 1
        max_nodes = conf['Chain length']['Max']*conf['Chain width']['Max'] \
                            - conf['Chain width']['Max'] + 1
        combos = []
        for combo in itertools.combinations_with_replacement(
                list(range(min_nodes, max_nodes+1)), conf['Number of chains']):
            if(sum(combo) == conf['Number of nodes']):
                combos.append(list(combo))
        chain_num_nodes_combo = random.choice(combos)
        random.shuffle(chain_num_nodes_combo)

        # Generate each chain
        chains = []
        for num_nodes_in_one_chain in chain_num_nodes_combo:
            chains.append(_generate_chain(conf, num_nodes_in_one_chain, G))
        
        # TODO: gen dag

        # (Optional) Use multi-period
        if('Use multi-period' in conf.keys()):
            random_set_period(conf, G)

        # Set execution time
        

        # (Optional) Use communication time
        if('Use communication time' in conf.keys()):
            for start_i, end_i in G.edges():
                G.edges[start_i, end_i]['communication_time'] = \
                        random_get_comm_time(conf)

        # (Optional) Use end-to-end deadline
        if('Use end-to-end deadline' in conf.keys()):
            set_end_to_end_deadlines(conf, G)

        write_dag(conf, dest_dir, f'dag_{dag_i}', G)


if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    config = load_chain_config(config_yaml_file)
    main(config, dest_dir)
