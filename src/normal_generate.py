import numpy as np
import networkx as nx
import random
import copy
import yaml
import os
from typing import List, Tuple, Union, Dict
from logging import getLogger

from src.utils import (
    option_parser, set_end_to_end_deadlines,
    random_get_comm,
    random_get_exec,
    choice_one_from_cfg
)
from src.file_handling_helper import load_normal_config, get_preprocessed_all_combo
from src.write_dag import write_dag
from src.random_set_period import random_set_period
from src.abbreviation import ToA, ToO


logger = getLogger(__name__)


def try_extend_dag(cfg, dag: nx.DiGraph) -> Tuple[bool, nx.DiGraph]:
    def get_min_of_range(param_cfg: Dict) -> Union[float, int]:
        if('Random' in param_cfg.keys()):
            return min(param_cfg['Random'])
        elif('Fixed' in param_cfg.keys()):
            return param_cfg['Fixed']

    def get_max_of_range(param_cfg: Dict) -> Union[float, int]:
        if('Random' in param_cfg.keys()):
            return max(param_cfg['Random'])
        elif('Fixed' in param_cfg.keys()):
            return param_cfg['Fixed']

    G = copy.deepcopy(dag)

    ### Determine end_num
    end_num = choice_one_from_cfg(cfg['Number of nodes'])
    if('Force merge to exit nodes' in cfg.keys()):
        end_num -= choice_one_from_cfg(cfg[ToO['FME']][ToO['NEX']])

    while(G.number_of_nodes() != end_num):
        leaves = [v for v, d in G.out_degree() if d == 0]

        ### Determine the number of next-depth nodes
        num_next = 0
        min_num = max(get_min_of_range(cfg['Out-degree']),
                      int(np.ceil(len(leaves)*get_min_of_range(cfg['Out-degree'])
                                  / get_max_of_range(cfg['In-degree']))))
        max_num = int(np.floor(len(leaves)*get_max_of_range(cfg['Out-degree'])
                               / get_min_of_range(cfg['In-degree'])))
        if(ToO['MNSD'] in cfg.keys()):
            max_num = min(max_num, choice_one_from_cfg(cfg[ToO['MNSD']]))

        if(G.number_of_nodes()+min_num <= end_num and
                G.number_of_nodes()+max_num >= end_num):
            num_next = end_num - G.number_of_nodes()
        elif(G.number_of_nodes()+min_num > end_num):
            return False, G
        else:
            num_next = random.randint(min_num, max_num)

        ### Add next-depth nodes
        next_nodes_i = [i for i in range(
                G.number_of_nodes(), G.number_of_nodes()+num_next)]
        for next_node_i in next_nodes_i:
            G.add_node(next_node_i)

        ### Determine the number of edges to next-depth nodes
        num_edges_to_next = random.randint(
                max(len(leaves)*get_min_of_range(cfg['Out-degree']),
                    num_next*get_min_of_range(cfg['In-degree'])),
                min(len(leaves)*get_max_of_range(cfg['Out-degree']),
                    num_next*get_max_of_range(cfg['In-degree'])))

        ### Add edges_to_next_depth
        add_edge_count = 0
        nodes_lack_out = copy.deepcopy(leaves)
        nodes_max_out = set()
        nodes_lack_in = copy.deepcopy(next_nodes_i)
        nodes_max_in = set()

        while(add_edge_count != num_edges_to_next):
            ### Check feasibility
            feasibility = False
            only_lack_out_feasibility = False
            for start_i in list(set(leaves) - nodes_max_out):
                if(nodes_lack_in):
                    targets = list(set(nodes_lack_in) - set(G.succ[start_i]))
                else:
                    targets = list(set(next_nodes_i)
                                   - set(G.succ[start_i])
                                   - nodes_max_in)
                if(targets):
                    feasibility = True
                    if(start_i in nodes_lack_out):
                        only_lack_out_feasibility = True
            if(not feasibility):
                return False, G

            ### Determine start_nodes_i
            start_nodes_i = []
            if(only_lack_out_feasibility):
                start_nodes_i = nodes_lack_out
            else:
                start_nodes_i = list(set(leaves)
                                     - set(nodes_lack_out)
                                     - nodes_max_out)

            for start_node_i in start_nodes_i:
                ### Determine target_node_i
                target_node_i = -1
                if(nodes_lack_in):
                    targets = list(set(nodes_lack_in)
                                   - set(G.succ[start_node_i]))
                else:
                    targets = list(set(next_nodes_i)
                                   - set(G.succ[start_node_i])
                                   - nodes_max_in)
                if(targets):
                    target_node_i = random.choice(targets)
                else:
                    continue

                ### Add edge
                G.add_edge(start_node_i, target_node_i)
                add_edge_count += 1
                if(G.out_degree(start_node_i) == get_min_of_range(cfg['Out-degree'])):
                    nodes_lack_out.remove(start_node_i)
                if(G.out_degree(start_node_i) == get_max_of_range(cfg['Out-degree'])):
                    nodes_max_out.add(start_node_i)
                if(G.in_degree(target_node_i) == get_min_of_range(cfg['In-degree'])):
                    nodes_lack_in.remove(target_node_i)
                if(G.in_degree(target_node_i) == get_max_of_range(cfg['In-degree'])):
                    nodes_max_in.add(target_node_i)
                if(add_edge_count == num_edges_to_next):
                    break

    return True, G


def force_merge_to_exit_nodes(conf, G: nx.DiGraph) -> None:
    leaves = [v for v, d in G.out_degree() if d == 0]
    exit_nodes_i = []
    for _ in range(choice_one_from_cfg(conf[ToO['FME']][ToO['NEX']])):
        exit_nodes_i.append(G.number_of_nodes())
        G.add_node(G.number_of_nodes())

    if(len(leaves) > len(exit_nodes_i)):
        no_in_degree_i = copy.deepcopy(exit_nodes_i)
        for leaf in leaves:
            if(no_in_degree_i):
                exit_node_i = random.choice(no_in_degree_i)
                G.add_edge(leaf, exit_node_i)
                no_in_degree_i.remove(exit_node_i)
            else:
                G.add_edge(leaf, random.choice(exit_nodes_i))
    else:
        while(exit_nodes_i):
            for leaf in leaves:
                if(not exit_nodes_i):
                    break
                exit_node_i = random.choice(exit_nodes_i)
                G.add_edge(leaf, exit_node_i)
                exit_nodes_i.remove(exit_node_i)


def generate(cfg, dest_dir):
    for dag_i in range(cfg['Number of DAGs']):
        G = nx.DiGraph()

        ### Add entry nodes
        for _ in range(choice_one_from_cfg(cfg['Number of entry nodes'])):
            G.add_node(G.number_of_nodes())

        ### Extend dag
        for num_try in range(max_try := 100):  # HACK
            result, extended_dag = try_extend_dag(cfg, G)
            if(result):
                G = extended_dag
                break
            if(num_try+1 == max_try):
                msg = ('Cannot create DAGs. '
                       'Please specify the feasible parameters.')
                logger.warning(msg)

        ### (Optional) Force merge to exit nodes
        if('Force merge to exit nodes' in cfg.keys()):
            force_merge_to_exit_nodes(cfg, G)

        ### (Optional) Use multi-period
        if('Use multi-period' in cfg.keys()):
            random_set_period(cfg, G)

        ### Set execution time
        # random_set_exec(cfg, G)  # TODO

        ### (Optional) Use communication time
        if('Use communication time' in cfg.keys()):
            for start_i, end_i in G.edges():
                G.edges[start_i, end_i]['comm'] = choice_one_from_cfg(cfg[ToO['UCT']])

        # (Optional) Use end-to-end deadline
        if('Use end-to-end deadline' in cfg.keys()):
            set_end_to_end_deadlines(cfg, G)

        write_dag(cfg, dest_dir, f'dag_{dag_i}', G)


if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    cfg = load_normal_config(config_yaml_file)

    all_combo_dir_name, all_combo_log, all_combo_cfg = get_preprocessed_all_combo(cfg, 'normal')
    for combo_dir_name, combo_log, combo_cfg in zip(all_combo_dir_name, all_combo_log, all_combo_cfg):
        dest_dir += f'/{combo_dir_name}'
        os.mkdir(dest_dir)
        with open(f'{dest_dir}/combination_log.yaml', 'w') as f:
            yaml.dump(combo_log, f)

        random.seed(cfg['Seed'])
        generate(combo_cfg, dest_dir)
