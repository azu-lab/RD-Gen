import argparse
from typing import Union, Dict
import networkx as nx
import random
import copy
import numpy as np

from common.file_handling_helper import load_normal_config
from common.write_dag import write_dag
from common.random_set_period import random_set_period


def option_parser() -> Union[argparse.FileType, str]:
    usage = f'[python] {__file__} --config_yaml_path [<path to config file>] --dest_dir [<destination directory>]'

    arg_parser = argparse.ArgumentParser(usage=usage)
    arg_parser.add_argument('--config_yaml_path',
                            type=argparse.FileType(("r")),
                            help='config file name (.yaml)')
    arg_parser.add_argument('--dest_dir',
                            type=str,
                            default='./',
                            help='destination directory')
    args = arg_parser.parse_args()

    return args.config_yaml_path, args.dest_dir


def random_get_exec_time(config) -> int:
    if('Use list' in config['Execution time'].keys()):
        return random.choice(config['Execution time']['Use list'])
    else:
        return random.randint(config['Execution time']['Min'],
                                    config['Execution time']['Max'])


def random_get_comm_time(config) -> int:
    if('Use list' in config['Use communication time'].keys()):
        return random.choice(config['Use communication time']['Use list'])
    else:
        return random.randint(config['Use communication time']['Min'],
                                    config['Use communication time']['Max'])


def try_extend_dag(config, dag : nx.DiGraph) -> Union[bool, nx.DiGraph]:
    G = copy.deepcopy(dag)
    end_num_node = config['Number of nodes']
    if('Force merge to exit nodes' in config.keys()):
        end_num_node -= config['Force merge to exit nodes']['Number of exit nodes']
    
    while(G.number_of_nodes() != end_num_node):
        leaves = [v for v, d in G.out_degree() if d == 0]
        
        # Determine num_next_depth
        num_next_depth_nodes = 0
        min_num = max(config['Out-degree']['Min'], 
                      int(np.ceil(len(leaves)*config['Out-degree']['Min'] / config['In-degree']['Max'])))
        max_num = int(np.floor(len(leaves)*config['Out-degree']['Max'] / config['In-degree']['Min']))
        if('Max number of same-depth nodes' in config.keys()):
            max_num = min(max_num, config['Max number of same-depth nodes'])

        if(G.number_of_nodes()+min_num >= end_num_node and
                G.number_of_nodes()+max_num <= end_num_node):
            num_next_depth_nodes = end_num_node - G.number_of_nodes()
            break
        elif(G.number_of_nodes() > end_num_node):
            return False, G
        else:
            num_next_depth_nodes = random.randint(min_num, max_num)
        
        # Add next_depth nodes
        next_nodes_i = [i for i in range(G.number_of_nodes(), G.number_of_nodes()+num_next_depth_nodes)]
        for next_node_i in next_nodes_i:
            G.add_node(next_node_i, execution_time=random_get_exec_time(config))
            
        # Determine num_edges_to_next_depth
        num_edges_to_next_depth = random.randint(
                max(len(leaves)*config['Out-degree']['Min'], num_next_depth_nodes*config['In-degree']['Min']),
                min(len(leaves)*config['Out-degree']['Max'], num_next_depth_nodes*config['In-degree']['Max']))
        
        # Add edges_to_next_depth
        add_edge_count = 0
        nodes_lack_out_degree = copy.deepcopy(leaves)
        nodes_max_out_degree = set()
        nodes_lack_in_degree = copy.deepcopy(next_nodes_i)
        nodes_max_in_degree = set()
        
        while(add_edge_count != num_edges_to_next_depth):
            # Check feasibility
            feasibility = False
            only_lack_out_degree_feasibility = False
            for start_i in list(set(leaves) - nodes_max_out_degree):
                if(nodes_lack_in_degree):
                    dests = list(set(nodes_lack_in_degree) - set(G.succ[start_i]))
                else:
                    dests = list(set(next_nodes_i) - set(G.succ[start_i]) - nodes_max_in_degree)
                if(dests):
                    feasibility = True
                    if(start_i in nodes_lack_out_degree):
                        only_lack_out_degree_feasibility = True
            if(feasibility == False):
                return False, G
            
            # Determine start_current_nodes
            start_current_nodes = []
            if(only_lack_out_degree_feasibility):
                start_current_nodes = nodes_lack_out_degree
            else:
                start_current_nodes = list(set(leaves)
                                                - set(nodes_lack_out_degree)
                                                - nodes_max_out_degree)
            
            for start_current_node_i in start_current_nodes:
                # Determine dest_next_node_i
                dest_next_node_i = -1
                if(nodes_lack_in_degree):
                    dests = list(set(nodes_lack_in_degree) - set(G.succ[start_current_node_i]))
                else:
                    dests = list(set(next_nodes_i)
                                    - set(G.succ[start_current_node_i])
                                    - nodes_max_in_degree)
                if(dests):
                    dest_next_node_i = random.choice(dests)
                else:
                    continue
    
                # Add edge
                G.add_edge(start_current_node_i, dest_next_node_i)
                add_edge_count += 1
                if(G.out_degree(start_current_node_i) == config['Out-degree']['Min']):
                    nodes_lack_out_degree.remove(start_current_node_i)
                if(G.out_degree(start_current_node_i) == config['Out-degree']['Max']):
                    nodes_max_out_degree.add(start_current_node_i)
                if(G.in_degree(dest_next_node_i) == config['In-degree']['Min']):
                    nodes_lack_in_degree.remove(dest_next_node_i)
                if(G.in_degree(dest_next_node_i) == config['In-degree']['Max']):
                    nodes_max_in_degree.add(dest_next_node_i)
                if(add_edge_count == num_edges_to_next_depth):
                    break
    
    return True, G


def force_merge_to_exit_nodes(config, G) -> None:
    leaves = [v for v, d in G.out_degree() if d == 0]
    exit_nodes_i = []
    for i in range(config['Force merge to exit nodes']['Number of exit nodes']):
        exit_nodes_i.append(G.number_of_nodes())
        G.add_node(G.number_of_nodes(), execution_time=random_get_exec_time(config))
    
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


def main(config, dest_dir):
    for dag_i in range(config['Number of DAGs']):
        random.seed(config['Initial seed'] + dag_i)
        G = nx.DiGraph()
        
        # Add entry nodes
        for i in range(config['Number of entry nodes']):
            G.add_node(G.number_of_nodes(), execution_time=random_get_exec_time(config))
        
        # Extend dag
        max_num_try = 100  # HACK
        for num_try in range(1, max_num_try+1):
            result, extended_dag = try_extend_dag(config, G)
            if(result):
                G = extended_dag
                break
            if(num_try == max_num_try):
                print("[Error] Cannot create DAGs. Please specify the feasible parameters.")
                exit(1)
        
        # (Optional) Force merge to exit nodes
        if('Force merge to exit nodes' in config.keys()):
            force_merge_to_exit_nodes(config, G)
        
        # (Optional) Use communication time
        if('Use communication time' in config.keys()):
            for start_i, end_i in G.edges():
                G.edges[start_i, end_i]['communication_time'] = random_get_comm_time(config)
        
        # (Optional) Use multi-period
        if('Use multi-period' in config.keys()):
            random_set_period(config, 'normal', G)
        
        # Output
        write_dag(config, dest_dir, f'dag_{dag_i}', G)


if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    config = load_normal_config(config_yaml_file)
    main(config, dest_dir)