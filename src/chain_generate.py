import numpy as np
import networkx as nx
import random
import copy
import itertools
from typing import List, Tuple

from utils import option_parser, random_set_e2e_deadline
from chain import _create_chain, vertically_link_chains, merge_chains
from file_handling_helper import load_chain_config
from src.output_dag import output_dag
from random_set_period import random_set_period


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
            chains.append(_create_chain(conf, num_nodes_in_one_chain, G))

        # (Optional) Vertically link chains
        if('Vertically link chains' in conf.keys()):
            vertically_link_chains(conf, chains, G)

        # (Optional) Merge chains
        if('Merge chains'in conf.keys()):
            merge_chains(conf, chains, G)

        # (Optional) Use communication time
        if('Use communication time' in conf.keys()):
            for start_i, end_i in G.edges():
                G.edges[start_i, end_i]['comm'] = \
                        random_get_comm(conf)

        # (Optional) Use multi-period
        if('Use multi-period' in conf.keys()):
            if(conf['Use multi-period']['Periodic type'] == 'Chain'):
                random_set_period(conf, G, chains)
            else:
                random_set_period(conf, G)

        # (Optional) Use end-to-end deadline
        if('Use end-to-end deadline' in conf.keys()):
            random_set_e2e_deadline(conf, G)

        output_dag(conf, dest_dir, f'dag_{dag_i}', G)


if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    config = load_chain_config(config_yaml_file)
    main(config, dest_dir)
