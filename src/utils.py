from operator import concat
import networkx as nx
import argparse
import random
import yaml
import os
import re
import copy
import itertools
import numpy as np

from typing import List, Tuple, Dict, Union

from src.abbreviation import PAC, to_ori


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


def get_args_from_tuple_str(combo_str: str) -> Dict:
    def convert_to_num(num_str: str) -> Union[int, float]:
        temp_float = float(num_str)
        if(temp_float.is_integer()):
            return int(temp_float)
        else:
            return temp_float
    
    combo_str = combo_str.replace('(', '')
    combo_str = combo_str.replace(')', '')
    combo_str = combo_str.replace(' ', '')

    args_dict = {'start': None, 'stop': None, 'step': None}
    for i, arg in enumerate(combo_str.split(',')):
        if(i==0 or 'start' in arg):
            args_dict['start'] = convert_to_num(arg.replace('start=', ''))
        elif(i==1 or 'stop' in arg):
            args_dict['stop'] = convert_to_num(arg.replace('stop=', ''))
        elif(i==2 or 'step' in arg):
            args_dict['step'] = convert_to_num(arg.replace('step=', ''))

    return args_dict


def get_all_combo_cfg(cfg, mode: str) -> Tuple[List[str], List[Dict]]:
    def get_children_param_name(top_param: str) -> Union[List[str], None]:
        if('Children' in format[top_param].keys()):
            return format[top_param]['Children'].keys()
        else:
            return None

    def create_combo_cfg(param_names: List[str], combo: List[Union[int, float]]) -> Dict:
        combo_cfg = copy.deepcopy(cfg)
        for param_name, value in zip(param_names, combo):
            if('_' in param_name):
                top_param_name = param_name.split('_')[0]
                child_param_name = param_name.split('_')[1]
                del combo_cfg[to_ori(top_param_name)][to_ori(child_param_name)]['Combination']
                combo_cfg[to_ori(top_param_name)][to_ori(child_param_name)]['Fixed'] = value
            else:
                del combo_cfg[to_ori(param_name)]['Combination']
                combo_cfg[to_ori(param_name)]['Fixed'] = value

        return combo_cfg

    def create_combo_dir_name(index: int,
                              param_names: List[str],
                              combo: List[Union[int, float]]
    ) -> str:
        def remove_parent(param_name: str) -> str:
            if('_' in param_name):
                return param_name.split('_')[1]
            else:
                return param_name

        combo_dir_name = None
        if(cfg['Naming of combination directory'] == 'Full spell'):
            for param_name, value in zip(param_names, combo):
                param_str_list = to_ori(remove_parent(param_name)).split(' ')
                param_str_list = [s.capitalize() for s in param_str_list]
                if(combo_dir_name):
                    combo_dir_name += f'_{"".join(param_str_list)}_{value}'
                else:
                    combo_dir_name = f'{"".join(param_str_list)}_{value}'
        elif(cfg['Naming of combination directory'] == 'Abbreviation'):
            for param_name, value in zip(param_names, combo):
                param_name = remove_parent(param_name)
                if(combo_dir_name):
                    combo_dir_name += f'_{param_name}_{value}'
                else:
                    combo_dir_name = f'{param_name}_{value}'
        elif(cfg['Naming of combination directory'] == 'Index of combination'):
            combo_dir_name = f'combination_{index}'

        return combo_dir_name


    if(mode == 'normal'):
        with open(f'{os.path.dirname(__file__)}/config_format/normal_format.yaml') as f:
            format = yaml.safe_load(f)
    if(mode == 'chain'):
        with open(f'{os.path.dirname(__file__)}/config_format/chain_format.yaml') as f:
            format = yaml.safe_load(f)

    # Search combination
    in_top_params = set(cfg.keys())
    combo_param_dict = {}
    for in_top_param in in_top_params - {'Number of DAGs', 'Seed', 'Naming of combination directory'}:
        if('Combination' in cfg[in_top_param].keys()):
            if(isinstance(cfg[in_top_param]['Combination'], str)):
                args = get_args_from_tuple_str(cfg[in_top_param]['Combination'])
                args['stop'] += args['step']  # include stop
                combo_param_dict[PAC[in_top_param]] = [round(v, 4) for v in np.arange(**args)]  # HACK
            else:
                combo_param_dict[PAC[in_top_param]] = cfg[in_top_param]['Combination']

        # Search children parameter
        elif(children_param_names := get_children_param_name(in_top_param)):
            for child_param_name in children_param_names:
                if(format[in_top_param]['Children'][child_param_name]['Type'] in ['int', 'float']
                        and child_param_name in cfg[in_top_param].keys()
                        and 'Combination' in cfg[in_top_param][child_param_name].keys()):
                    if(isinstance(cfg[in_top_param][child_param_name]['Combination'], str)):
                        args = get_args_from_tuple_str(cfg[in_top_param][child_param_name]['Combination'])
                        args['stop'] += args['step']  # include stop
                        combo_param_dict[f'{PAC[in_top_param]}_{PAC[child_param_name]}'] = [round(v, 4) for v in np.arange(**args)]  # HACK
                    else:
                        combo_param_dict[f'{PAC[in_top_param]}_{PAC[child_param_name]}'] = cfg[in_top_param][child_param_name]['Combination']

    dest_dir_name = []
    all_combo_cfg = []
    for i, combo in enumerate(list(itertools.product(*list(combo_param_dict.values())))):
        dest_dir_name.append(create_combo_dir_name(i, list(combo_param_dict.keys()), list(combo)))
        all_combo_cfg.append(create_combo_cfg(list(combo_param_dict.keys()), list(combo)))

    return dest_dir_name, all_combo_cfg


def _get_cp_and_cp_len(dag: nx.DiGraph, source, exit) -> Tuple[List[int], int]:
    cp = []
    cp_len = 0

    paths = nx.all_simple_paths(dag, source=source, target=exit)
    for path in paths:
        path_len = 0
        for i in range(len(path)):
            path_len += dag.nodes[path[i]]['exec']
            if(i != len(path)-1 and
                    'comm' in list(dag.edges[path[i], path[i+1]].keys())):
                path_len += dag.edges[path[i], path[i+1]]['comm']
        if(path_len > cp_len):
            cp = path
            cp_len = path_len

    return cp, cp_len


def set_end_to_end_deadlines(conf, G: nx.DiGraph) -> None:
    if('Use multi-period' in conf.keys() and
            'Ratio of deadlines to max period' in conf['Use end-to-end deadline'].keys()):
        max_period = max((nx.get_node_attributes(G, 'period')).values())
        for exit_i in [v for v, d in G.out_degree() if d == 0]:
            G.nodes[exit_i]['deadline'] = \
                    int(max_period * conf['Use end-to-end deadline']['Ratio of deadlines to max period'])

    elif('Ratio of deadlines to critical path length' in conf['Use end-to-end deadline'].keys()):
        for exit_i in [v for v, d in G.out_degree() if d == 0]:
            max_cp_len = 0
            for entry_i in [v for v, d in G.in_degree() if d == 0]:
                _, cp_len = _get_cp_and_cp_len(G, entry_i, exit_i)
                if(cp_len > max_cp_len):
                    max_cp_len = cp_len
            G.nodes[exit_i]['deadline'] = int(
                    max_cp_len
                    * conf['Use end-to-end deadline']['Ratio of deadlines to critical path length'])


def random_get_comm_time(conf) -> int:
    if('Use list' in conf['Use communication time'].keys()):
        return random.choice(conf['Use communication time']['Use list'])
    else:
        return random.randint(conf['Use communication time']['Min'],
                              conf['Use communication time']['Max'])


def random_get_exec_time(conf) -> int:
    if('Use list' in conf['Execution time'].keys()):
        return random.choice(conf['Execution time']['Use list'])
    else:
        return random.randint(conf['Execution time']['Min'],
                              conf['Execution time']['Max'])


def _get_settable_min_exec(conf) -> int:
    if('Use list' in conf['Execution time'].keys()):
        return min(conf['Execution time']['Use list'])
    else:
        return conf['Execution time']['Min']


def _get_settable_min_comm(conf) -> int:
    if('Use list' in conf['Use communication time'].keys()):
        return min(conf['Use communication time']['Use list'])
    else:
        return conf['Use communication time']['Min']


def _get_settable_max_period(conf) -> int:
    if('Use list' in conf['Use multi-period'].keys()):
        return max(conf['Use multi-period']['Use list'])
    else:
        return conf['Use multi-period']['Max']
