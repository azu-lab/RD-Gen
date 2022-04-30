import numpy as np
import networkx as nx
import random
import copy
import os
import yaml
import itertools
from typing import List, Tuple
from logging import getLogger

from src.utils import (
    option_parser,
    random_set_e2e_deadline,
    choice_one_from_cfg,
    get_max_of_range,
    get_min_of_range
)
from src.chain import generate_single_chain, vertically_link_chains, merge_chains
from src.file_handling_helper import load_chain_config, get_preprocessed_all_combo
from src.output_dag import output_dag
from src.random_set_period import random_set_period
from src.abbreviation import ToO
from src.exceptions import NoSettablePeriodError, InvalidConfigError


logger = getLogger(__name__)


def generate(cfg, dest_dir):
    ### Generate DAGs
    for dag_i in range(cfg['Number of DAGs']):
        G = nx.DiGraph()

        ### Determine the number of nodes in each chain
        min_nodes = get_min_of_range(cfg[ToO['CL']]) + get_min_of_range(cfg[ToO['CW']]) - 1
        max_nodes = (get_max_of_range(cfg[ToO['CL']])
                     * get_max_of_range(cfg[ToO['CW']])
                     - get_max_of_range(cfg[ToO['CW']])
                     + 1)
        combos = []
        for combo in itertools.combinations_with_replacement(
                list(range(min_nodes, max_nodes+1)), choice_one_from_cfg(cfg[ToO['NC']])):
            if(sum(combo) == choice_one_from_cfg(cfg[ToO['NN']])):
                combos.append(list(combo))
        chain_num_nodes_combo = random.choice(combos)

        ### Generate each chain
        chains = []
        for num_nodes_in_one_chain in chain_num_nodes_combo:
            chains.append(generate_single_chain(cfg, num_nodes_in_one_chain, G))

        ### (Optional) Vertically link chains
        if('Vertically link chains' in cfg.keys()):
            vertically_link_chains(cfg, chains, G)

        ### (Optional) Merge chains
        if('Merge chains'in cfg.keys()):
            merge_chains(cfg, chains, G)

        ### (Optional) Use multi-period
        if('Use multi-period' in cfg.keys()):
            random_set_period(cfg, G, chains)

        ### (Optional) Use communication time
        if('Use communication time' in cfg.keys()):
            for start_i, end_i in G.edges():
                G.edges[start_i, end_i]['comm'] = choice_one_from_cfg(cfg[ToO['UCT']])

        ### Set execution time
        try:
            for chain in chains:
                    chain.random_set_exec(cfg, G)
        except NoSettablePeriodError:
            msg = ('No Settable Period. '
                    'Please specify the feasible parameters.'
                    'Parameter combination file: '
                    f'{dest_dir}/combination_log.yaml')
            raise InvalidConfigError(msg)

        # (Optional) Use end-to-end deadline
        if('Use end-to-end deadline' in cfg.keys()):
            random_set_e2e_deadline(cfg, G)

        output_dag(cfg, dest_dir, f'dag_{dag_i}', G)


if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    cfg = load_chain_config(config_yaml_file)
    
    all_combo_dir_name, all_combo_log, all_combo_cfg = get_preprocessed_all_combo(cfg, 'chain')
    for combo_dir_name, combo_log, combo_cfg in zip(all_combo_dir_name, all_combo_log, all_combo_cfg):
        combo_dest_dir = dest_dir + f'/{combo_dir_name}'
        os.mkdir(combo_dest_dir)
        with open(f'{combo_dest_dir}/combination_log.yaml', 'w') as f:
            yaml.dump(combo_log, f)

        random.seed(cfg['Seed'])
        try:
            generate(combo_cfg, combo_dest_dir)
        except InvalidConfigError as e:
            logger.warning(e.message)
