import numpy as np
import networkx as nx
import random
import copy
import yaml
import json
import itertools
from typing import List, Tuple
from networkx.readwrite import json_graph

from utils import option_parser, set_end_to_end_deadlines, random_get_comm_time, random_get_exec_time
from file_handling_helper import load_chain_config
from write_dag import write_dag
from random_set_period import random_set_period


def main(conf, dest_dir):
    for dag_i in range(conf['Number of DAGs']):
        random.seed(conf['Initial seed'] + dag_i)
        G = nx.DiGraph()

        # Determine the number of nodes in each chain
        min_nodes = conf['Chain length']['Min'] + conf['Chain width']['Min'] - 1
        max_nodes = conf['Chain length']['Max']*conf['Chain width']['Max'] \
                            - conf['Chain width']['Max'] + 1
        combination_options = []
        for combination in itertools.combinations(
                list(range(min_nodes, max_nodes+1)), conf['Number of chains']):
            if(sum(combination) == conf['Number of nodes']):
                combination_options.append(list(combination))
        combination = random.choice(combination_options)

        
        # TODO: gen dag

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
            random_set_period(conf, G)

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
    config = load_chain_config(config_yaml_file)
    main(config, dest_dir)
