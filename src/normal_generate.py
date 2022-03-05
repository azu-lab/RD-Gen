import argparse
import numpy as np
import networkx as nx
import random
import copy
import yaml
import json
from typing import List, Tuple
from networkx.readwrite import json_graph

from file_handling_helper import load_normal_config
from write_dag import write_dag
from random_set_period import random_set_period


def option_parser() -> Tuple[argparse.FileType, str]:
    usage = f'[python] {__file__} \
              --config_yaml_path [<path to config file>] \
              --dest_dir [<destination directory>]'

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


def random_get_exec_time(conf) -> int:
    if('Use list' in conf['Execution time'].keys()):
        return random.choice(conf['Execution time']['Use list'])
    else:
        return random.randint(conf['Execution time']['Min'],
                              conf['Execution time']['Max'])


def random_get_comm_time(conf) -> int:
    if('Use list' in conf['Use communication time'].keys()):
        return random.choice(conf['Use communication time']['Use list'])
    else:
        return random.randint(conf['Use communication time']['Min'],
                              conf['Use communication time']['Max'])


def try_extend_dag(conf, dag: nx.DiGraph) -> Tuple[bool, nx.DiGraph]:
    dag = copy.deepcopy(dag)
    end_num = conf['Number of nodes']
    if('Force merge to exit nodes' in conf.keys()):
        end_num -= conf['Force merge to exit nodes']['Number of exit nodes']

    while(dag.number_of_nodes() != end_num):
        leaves = [v for v, d in dag.out_degree() if d == 0]

        # Determine the number of next-depth nodes
        num_next = 0
        min_num = max(conf['Out-degree']['Min'],
                      int(np.ceil(len(leaves)*conf['Out-degree']['Min']
                                  / conf['In-degree']['Max'])))
        max_num = int(np.floor(len(leaves)*conf['Out-degree']['Max']
                               / conf['In-degree']['Min']))
        if('Max number of same-depth nodes' in conf.keys()):
            max_num = min(max_num, conf['Max number of same-depth nodes'])

        if(dag.number_of_nodes()+min_num <= end_num and
                dag.number_of_nodes()+max_num >= end_num):
            num_next = end_num - dag.number_of_nodes()
        elif(dag.number_of_nodes()+min_num > end_num):
            return False, dag
        else:
            num_next = random.randint(min_num, max_num)

        # Add next-depth nodes
        next_nodes_i = [i for i in range(
                dag.number_of_nodes(), dag.number_of_nodes()+num_next)]
        for next_node_i in next_nodes_i:
            dag.add_node(next_node_i,
                         execution_time=random_get_exec_time(conf))

        # Determine the number of edges to next-depth nodes
        num_edges_to_next = random.randint(
                max(len(leaves)*conf['Out-degree']['Min'],
                    num_next*conf['In-degree']['Min']),
                min(len(leaves)*conf['Out-degree']['Max'],
                    num_next*conf['In-degree']['Max']))

        # Add edges_to_next_depth
        add_edge_count = 0
        nodes_lack_out = copy.deepcopy(leaves)
        nodes_max_out = set()
        nodes_lack_in = copy.deepcopy(next_nodes_i)
        nodes_max_in = set()

        while(add_edge_count != num_edges_to_next):
            # Check feasibility
            feasibility = False
            only_lack_out_feasibility = False
            for start_i in list(set(leaves) - nodes_max_out):
                if(nodes_lack_in):
                    targets = list(set(nodes_lack_in) - set(dag.succ[start_i]))
                else:
                    targets = list(set(next_nodes_i)
                                   - set(dag.succ[start_i])
                                   - nodes_max_in)
                if(targets):
                    feasibility = True
                    if(start_i in nodes_lack_out):
                        only_lack_out_feasibility = True
            if(not feasibility):
                return False, dag

            # Determine start_nodes_i
            start_nodes_i = []
            if(only_lack_out_feasibility):
                start_nodes_i = nodes_lack_out
            else:
                start_nodes_i = list(set(leaves)
                                     - set(nodes_lack_out)
                                     - nodes_max_out)

            for start_node_i in start_nodes_i:
                # Determine target_node_i
                target_node_i = -1
                if(nodes_lack_in):
                    targets = list(set(nodes_lack_in)
                                   - set(dag.succ[start_node_i]))
                else:
                    targets = list(set(next_nodes_i)
                                   - set(dag.succ[start_node_i])
                                   - nodes_max_in)
                if(targets):
                    target_node_i = random.choice(targets)
                else:
                    continue

                # Add edge
                dag.add_edge(start_node_i, target_node_i)
                add_edge_count += 1
                if(dag.out_degree(start_node_i) == conf['Out-degree']['Min']):
                    nodes_lack_out.remove(start_node_i)
                if(dag.out_degree(start_node_i) == conf['Out-degree']['Max']):
                    nodes_max_out.add(start_node_i)
                if(dag.in_degree(target_node_i) == conf['In-degree']['Min']):
                    nodes_lack_in.remove(target_node_i)
                if(dag.in_degree(target_node_i) == conf['In-degree']['Max']):
                    nodes_max_in.add(target_node_i)
                if(add_edge_count == num_edges_to_next):
                    break

    return True, dag


def force_merge_to_exit_nodes(conf, G: nx.DiGraph) -> None:
    leaves = [v for v, d in G.out_degree() if d == 0]
    exit_nodes_i = []
    for i in range(conf['Force merge to exit nodes']['Number of exit nodes']):
        exit_nodes_i.append(G.number_of_nodes())
        G.add_node(G.number_of_nodes(),
                   execution_time=random_get_exec_time(conf))

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


def get_cp_and_cp_len(dag: nx.DiGraph, source, exit) -> Tuple[List[int], int]:
    cp = []
    cp_len = 0

    paths = nx.all_simple_paths(dag, source=source, target=exit)
    for path in paths:
        path_len = 0
        for i in range(len(path)):
            path_len += dag.nodes[path[i]]['execution_time']
            if(i != len(path)-1 and
                    'communication_time' in list(dag.nodes[path[i]].keys())):
                path_len += dag.edges[path[i], path[i+1]]['communication_time']
        if(path_len > cp_len):
            cp = path
            cp_len = path_len

    return cp, cp_len


def set_end_to_end_deadlines(conf, G: nx.DiGraph) -> None:
    for exit_i in [v for v, d in G.out_degree() if d == 0]:
        max_cp_len = 0
        for entry_i in [v for v, d in G.in_degree() if d == 0]:
            _, cp_len = get_cp_and_cp_len(G, entry_i, exit_i)
            if(cp_len > max_cp_len):
                max_cp_len = cp_len

        G.nodes[exit_i]['deadline'] = int(
                max_cp_len
                * conf['Use end-to-end deadline']['Ratio of deadlines to critical path length'])


def main(conf, dest_dir):
    for dag_i in range(conf['Number of DAGs']):
        random.seed(conf['Initial seed'] + dag_i)
        G = nx.DiGraph()

        # Add entry nodes
        for i in range(conf['Number of entry nodes']):
            G.add_node(G.number_of_nodes(),
                       execution_time=random_get_exec_time(conf))

        # Extend dag
        max_num_try = 100  # HACK
        for num_try in range(1, max_num_try+1):
            result, extended_dag = try_extend_dag(conf, G)
            if(result):
                G = extended_dag
                break
            if(num_try == max_num_try):
                print("[Error] Cannot create DAGs. \
                       Please specify the feasible parameters.")
                exit(1)

        # (Optional) Force merge to exit nodes
        if('Force merge to exit nodes' in conf.keys()):
            force_merge_to_exit_nodes(conf, G)

        # (Optional) Use communication time
        if('Use communication time' in conf.keys()):
            for start_i, end_i in G.edges():
                G.edges[start_i, end_i]['communication_time'] = \
                        random_get_comm_time(conf)

        # (Optional) Use end-to-end deadline
        if('Use end-to-end deadline' in conf.keys()):
            set_end_to_end_deadlines(conf, G)

        # (Optional) Use multi-period
        if('Use multi-period' in conf.keys()):
            random_set_period(conf, 'normal', G)

        # Output
        dag_formats = [k for k, v in conf['DAG format'].items() if v]
        if('xml' in dag_formats):
            nx.write_graphml_xml(G, f'{dest_dir}/dag_{dag_i}.xml')
        if('dot' in dag_formats):
            nx.drawing.nx_pydot.write_dot(G, f'{dest_dir}/dag_{dag_i}.dot')
        if('json' in dag_formats):
            data = json_graph.node_link_data(G)
            s = json.dumps(data)
            with open(f'{dest_dir}/dag_{dag_i}.json', 'w') as f:
                json.dump(s, f)
        if('yaml' in dag_formats):
            data = json_graph.node_link_data(G)
            s = json.dumps(data)
            dic = json.loads(s)
            with open(f'{dest_dir}/dag_{dag_i}.yaml', 'w') as f:
                yaml.dump(dic, f)

        write_dag(conf, dest_dir, f'dag_{dag_i}', G)


if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    config = load_normal_config(config_yaml_file)
    main(config, dest_dir)
