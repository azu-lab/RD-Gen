import argparse
import file_handling_helper
from typing import Union, Dict, Tuple
import networkx as nx
import random
import copy
import numpy as np
import pydot
from write_dag import write_dag


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


def random_get_exec_time(config : Dict) -> int:
    if('Use list' in config['Execution time'].keys()):
        return random.choice(config['Execution time']['Use list'])
    else:
        return random.randint(config['Execution time']['Min'], config['Execution time']['Max'])


def try_extend_dag(config, dag : nx.DiGraph) -> Union[bool, nx.DiGraph]:
    G = copy.deepcopy(dag)
    end_num_node = config['Number of nodes']
    if('Force merge to exit nodes' in config.keys()):
        end_num_node -= config['Force merge to exit nodes']['Number of exit nodes']
    
    while(G.number_of_nodes() != end_num_node):
        leaves = [v for v, d in G.out_degree() if d == 0]
        
        # Determine num_next_level
        num_next_level_nodes = 0
        min_num = max(config['Out-degree']['Min'], 
                      int(np.ceil(len(leaves)*config['Out-degree']['Min'] / config['In-degree']['Max'])))
        max_num = int(np.floor(len(leaves)*config['Out-degree']['Max'] / config['In-degree']['Min']))

        if(G.number_of_nodes()+min_num >= end_num_node and
                G.number_of_nodes()+max_num <= end_num_node):
            for num in range(min_num, max_num):
                if(G.number_of_nodes()+num == end_num_node):
                    num_next_level_nodes = num
                    break
        elif(G.number_of_nodes() > end_num_node):
            return False, G
        else:
            num_next_level_nodes = random.randint(min_num, max_num)
        
        # Add next_level nodes
        next_nodes_i = [i for i in range(G.number_of_nodes(), G.number_of_nodes()+num_next_level_nodes)]
        for next_node_i in next_nodes_i:
            G.add_node(next_node_i, execution_time=random_get_exec_time(config), timer_driven=False)
            
        # Determine num_edges_to_next_level
        num_edges_to_next_level = random.randint(
                max(len(leaves)*config['Out-degree']['Min'], num_next_level_nodes*config['In-degree']['Min']),
                min(len(leaves)*config['Out-degree']['Max'], num_next_level_nodes*config['In-degree']['Max']))
        
        # Add edges_to_next_level
        add_edge_count = 0
        nodes_lack_out_degree = copy.deepcopy(leaves)
        nodes_max_out_degree = set()
        nodes_lack_in_degree = copy.deepcopy(next_nodes_i)
        nodes_max_in_degree = set()
        
        while(add_edge_count != num_edges_to_next_level):
            # Check feasibility
            feasibility = False
            only_lack_out_degree_feasibility = False
            for start_i in list(set(leaves) - nodes_max_out_degree):
                if(nodes_lack_in_degree):
                    dests = list(set(nodes_lack_in_degree) - set(G.succ[start_i]))
                else:
                    dests = list(set(next_nodes_i) - set(G.succ[start_i]) - nodes_max_in_degree)
                if(len(dests) > 0):
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
                if(add_edge_count == num_edges_to_next_level):
                    break
    
    return True, G


def main(config, dest_dir):
    # Validation check of In-degree and Out-degree
    if(config['In-degree']['Max'] < config['Out-degree']['Min']):
        print("[Error] Please increase 'Max' of 'In-degree' or decrease 'Min' of 'Out-degree'.")
        exit(1)
    if(config['Out-degree']['Max'] < config['In-degree']['Min']):
        print("[Error] Please increase 'Max' of 'Out-degree' or decrease 'Min' of 'In-degree'.")
        exit(1)
    
    # Generate DAGs
    for dag_i in range(config['Number of DAGs']):
        random.seed(config['Initial seed'] + dag_i)
        G = nx.DiGraph()
        
        # Add entry nodes
        for i in range(config['Number of entry nodes']):
            G.add_node(G.number_of_nodes(), execution_time=random_get_exec_time(config), timer_driven=False)
        
        # Extend dag
        max_num_try = 100  # HACK
        for num_try in range(1, max_num_try+1):
            result, extended_dag = try_extend_dag(config, G)
            if(result):
                G = extended_dag
                break
            
            if(num_try == max_num_try):
                print("[Error] ぴったりの DAG を作れません")
                exit(1)
        
        write_dag(f'dag_{dag_i}', G)
        
        # TODO: 強制マージなら exit node を追加し、後続ノードがないノードをすべて繋ぐ
        # TODO: 通信時間を使うなら、通信時間をランダムに決める
        # TODO: 最後に Periodic type に応じて、周期タスクにする

if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    config = file_handling_helper.load_normal_config(config_yaml_file)
    main(config, dest_dir)