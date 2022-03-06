import sys
import yaml
import numpy as np
from typing import Dict, List, Union


'''
'Requirement':'compulsory', 'optional', 'default', or [{'A'}, {'B'}, {'C'}]
    - 'default' : If not specified, default parameter is used.
    - [{'A'}, {'B'}, {'C'}]:  At least one of 'A', 'B', or 'C' must be specified.
'''
normal_format = {
    'Number of DAGs': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
    'Initial seed': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
    'Number of nodes': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
    'Number of entry nodes': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
    'In-degree': {'Requirement':'compulsory', 'Children':{
        'Min': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
        'Max': {'Requirement':'compulsory', 'Children':None, 'Type':'int'}}},
    'Out-degree': {'Requirement':'compulsory', 'Children':{
        'Min': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
        'Max': {'Requirement':'compulsory', 'Children':None, 'Type':'int'}}},
    'Execution time': {'Requirement':'compulsory', 'Children':{
        'Min': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Max': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Use list': {'Requirement': [{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'List[int]'}}},
    'Max number of same-depth nodes': {'Requirement':'optional', 'Children':None, 'Type':'int'},
    'Force merge to exit nodes': {'Requirement':'optional', 'Children':{
        'Number of exit nodes': {'Requirement':'compulsory', 'Children':None, 'Type':'int'}}},
    'Use end-to-end deadline': {'Requirement':'optional', 'Children':{
        'Ratio of deadlines to critical path length': {'Requirement':[{'Ratio of deadlines to critical path length'},{'Ratio of deadlines to max period'}], 'Children':None, 'Type':'float'},
        'Ratio of deadlines to max period': {'Requirement':[{'Ratio of deadlines to critical path length'},{'Ratio of deadlines to max period'}], 'Children':None, 'Type':'float'}}},
    'Use communication time': {'Requirement':'optional', 'Children':{
        'Min': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Max': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Use list': {'Requirement': [{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'List[int]'}}},
    'Use multi-period': {'Requirement':'optional', 'Children':{
        'Periodic type': {'Requirement':'compulsory', 'Children':None, 'Type':['Entry', 'All']},
        'Min': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Max': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Use list': {'Requirement': [{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'List[int]'},
        'Entry node periods': {'Requirement':'optional', 'Children':None, 'Type':'List[int]'},
        'Exit node periods': {'Requirement':'optional', 'Children':None, 'Type':'List[int]'},
        'Max ratio of execution time to period': {'Requirement':'compulsory', 'Children':None, 'Type':'float'},
        'Descendants have larger period': {'Requirement':'optional', 'Children':None, 'Type':'bool'}}},
    'DAG format': {'Requirement':'default', 'Children':{
        'yaml': {'Requirement':'default', 'Children':None, 'Type':'bool', 'Default':True},
        'json': {'Requirement':'optional', 'Children':None, 'Type':'bool'},
        'xml': {'Requirement':'optional', 'Children':None, 'Type':'bool'},
        'dot': {'Requirement':'optional', 'Children':None, 'Type':'bool'}}},
    'Figure format': {'Requirement':'default', 'Children':{
        'pdf': {'Requirement':'default', 'Children':None, 'Type':'bool', 'Default':True},
        'png': {'Requirement':'optional', 'Children':None, 'Type':'bool'},
        'svg': {'Requirement':'optional', 'Children':None, 'Type':'bool'}}}
}


chain_format = {
    'Number of DAGs': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
    'Initial seed': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
    'Number of nodes': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
    'Number of chains': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
    'Chain length': {'Requirement':'compulsory', 'Children':{
        'Min': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
        'Max': {'Requirement':'compulsory', 'Children':None, 'Type':'int'}}},
    'Chain width': {'Requirement':'compulsory', 'Children':{
        'Min': {'Requirement':'compulsory', 'Children':None, 'Type':'int'},
        'Max': {'Requirement':'compulsory', 'Children':None, 'Type':'int'}}},
    'Execution time': {'Requirement':'compulsory', 'Children':{
        'Min': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Max': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Use list': {'Requirement': [{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'List[int]'}}},
    'Vertically link chains': {'Requirement':'optional', 'Children':{
        'Max level of vertical links': {'Requirement':[{'Max level of vertical links'}, {'Max number of parallel chains'}], 'Children':None, 'Type':'int'},
        'Max number of parallel chains': {'Requirement':[{'Max level of vertical links'}, {'Max number of parallel chains'}], 'Children':None, 'Type':'int'}}},
    'Merge chains': {'Requirement':'optional', 'Children':{
        'Middle of chain': {'Requirement':[{'Middle of chain'}, {'Exit nodes'}, {'Head of next level chain'}], 'Children':None, 'Type':'bool'},
        'Exit nodes': {'Requirement':[{'Middle of chain'}, {'Exit nodes'}, {'Head of next level chain'}], 'Children':None, 'Type':'bool'},
        'Head of next level chain': {'Requirement':[{'Middle of chain'}, {'Exit nodes'}, {'Head of next level chain'}], 'Children':None, 'Type':'bool'}}},
    'Number of entry nodes': {'Requirement':'optional', 'Children':None, 'Type':'int'},
    'Number of exit nodes': {'Requirement':'optional', 'Children':None, 'Type':'int'},
    'Use end-to-end deadline': {'Requirement':'optional', 'Children':{
        'Ratio of deadlines to critical path length': {'Requirement':[{'Ratio of deadlines to critical path length'},{'Ratio of deadlines to max period'}], 'Children':None, 'Type':'float'},
        'Ratio of deadlines to max period': {'Requirement':[{'Ratio of deadlines to critical path length'},{'Ratio of deadlines to max period'}], 'Children':None, 'Type':'float'}}},
    'Use communication time': {'Requirement':'optional', 'Children':{
        'Min': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Max': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Use list': {'Requirement': [{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'List[int]'}}},
    'Use multi-period': {'Requirement':'optional', 'Children':{
        'Periodic type': {'Requirement':'compulsory', 'Children':None, 'Type':['Entry', 'All', 'Chain']},
        'Min': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Max': {'Requirement':[{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'int'},
        'Use list': {'Requirement': [{'Min','Max'}, {'Use list'}], 'Children':None, 'Type':'List[int]'},
        'Entry node periods': {'Requirement':'optional', 'Children':None, 'Type':'List[int]'},
        'Exit node periods': {'Requirement':'optional', 'Children':None, 'Type':'List[int]'},
        'Max ratio of execution time to period': {'Requirement':'compulsory', 'Children':None, 'Type':'float'},
        'Descendants have larger period': {'Requirement':'optional', 'Children':None, 'Type':'bool'}}},
    'DAG format': {'Requirement':'default', 'Children':{
        'yaml': {'Requirement':'default', 'Children':None, 'Type':'bool', 'Default':True},
        'json': {'Requirement':'optional', 'Children':None, 'Type':'bool'},
        'xml': {'Requirement':'optional', 'Children':None, 'Type':'bool'},
        'dot': {'Requirement':'optional', 'Children':None, 'Type':'bool'}}},
    'Figure format': {'Requirement':'default', 'Children':{
        'pdf': {'Requirement':'default', 'Children':None, 'Type':'bool', 'Default':True},
        'png': {'Requirement':'optional', 'Children':None, 'Type':'bool'},
        'svg': {'Requirement':'optional', 'Children':None, 'Type':'bool'}}}
}


def _load_yaml(config_yaml_file):
    try:
        config = yaml.safe_load(config_yaml_file)
    except yaml.YAMLError:
        print(f"[Error] when loading yaml: {sys.exc_info()}", file=sys.stderr)
        exit(1)

    return config


def _get_formatted_type_str(type: Union[str, List[str]]) -> str:
    formatted_type_str = ''
    if(isinstance(type, list)):
        for i, opt_str in enumerate(type):
            if(i != len(type)-1):
                formatted_type_str += f"\'{opt_str}\' or "
            else:
                formatted_type_str += f"\'{opt_str}\'"
    elif(type == 'List[int]'):
        formatted_type_str = '[<int>, ..., <int>]'
    else:
        formatted_type_str = f"<{type}>"

    return formatted_type_str


def _show_config_format(mode: str) -> None:
    def __show_format_from_top_keys(top_keys : list) -> None:
        for top_key in top_keys:
            if(format[top_key]['Children']):
                print(f'{top_key}:')
                for child_k, child_v in format[top_key]['Children'].items():
                    print(f"  {child_k}: {_get_formatted_type_str(child_v['Type'])}")
            else:
                print(f"{top_key}: {_get_formatted_type_str(format[top_key]['Type'])}")

    if(mode == 'normal'):
        format = normal_format
    elif(mode == 'chain'):
        format = chain_format
        pass
    
    print('\n')
    print('Please describe the configuration file as follows:')
    print('--------------------------------------------------')
    print('# Compulsory parameters')
    compulsory_params = [k for k, v in format.items() if v['Requirement'] == 'compulsory']
    __show_format_from_top_keys(compulsory_params)
    print('\n')
    print('# Optional parameters')
    optional_params = [k for k, v in format.items() if v['Requirement'] == 'optional']
    __show_format_from_top_keys(optional_params)
    print('\n')
    print('# Output formats')
    output_formats = [k for k, v in format.items() if v['Requirement'] == 'default']
    __show_format_from_top_keys(output_formats)
    print('--------------------------------------------------')
    print('\n')


def _error_not_specified(mode: str, param_name: str, parent_param='') -> None:
    if(parent_param == ''):
        print(f"[Error] '{param_name}' is not specified.")
    else:
        print(f"[Error] '{parent_param}: {param_name}' is not specified.")

    _show_config_format(mode)
    exit(1)


def _error_at_least_one(mode: str, options: list, parent_param='') -> None:
    option_str_list = []
    for option in options:
        option_str_list.append('(' + ','.join(option) + ')')
    
    options_str = ' or '.join(option_str_list)

    if(parent_param == ''):
        print(f"[Error] At least one of '{options_str}' must be specified.")
    else:
        print(f"[Error] At least one of '{parent_param}: {options_str}' must be specified.")

    _show_config_format(mode)
    exit(1)


def _error_invalid_type(mode: str, param_name: str, correct_type: Union[str, List[str]], parent_param='') -> None:
    if(parent_param == ''):
        print(f"[Error] Type of '{param_name}' must be {_get_formatted_type_str(correct_type)}.")
    else:
        print(f"[Error] Type of '{parent_param}: {param_name}' must be {_get_formatted_type_str(correct_type)}.")

    _show_config_format(mode)
    exit(1)


def _is_correct_type(value, correct_type: Union[str, List[str]]) -> bool:
    if(correct_type == 'int'):
        if(not isinstance(value, int)):
            return False
    elif(correct_type == 'float'):
        if(not isinstance(value, float)):
            return False
    elif(correct_type == 'bool'):
        if(not isinstance(value, bool)):
            return False
    elif(correct_type == 'List[int]'):
        if(not isinstance(value, list)):
            return False
        for v in value:
            if(not isinstance(v, int)):
                return False
    elif(isinstance(correct_type, list)):
        if(value not in correct_type):
            return False

    return True


def _warn_use_default(param_name: str, default_param_name: str) -> None:
    print(f"[Waring] '{param_name}' is not specified. Use the default, '{default_param_name}'")


def _check_config_format(mode: str, conf) -> None:
    def __check_children_requirements(top_key) -> None:
        # Initialize variables
        format_children = format[top_key]['Children']
        children_comp_keys = [k for k, v in format_children.items()
                                    if v['Requirement'] == 'compulsory']
        minimum_list = []
        for child_v in format_children.values():
            if(isinstance(child_v['Requirement'], list)):
                minimum_list = child_v['Requirement']
                break
        try:
            input_children_keys = conf[top_key].keys()
        except AttributeError:
            if(children_comp_keys):
                _error_not_specified(mode, children_comp_keys[0], top_key)
            if(minimum_list):
                _error_at_least_one(mode, minimum_list, top_key)

        # Check children's compulsory parameter exists
        if(children_comp_keys):
            for child_comp_key in children_comp_keys:
                if(child_comp_key not in input_children_keys):
                    _error_not_specified(mode, child_comp_key, top_key)

        # Check children's minimum parameter exists
        if(minimum_list):
            min_param_exist_flag = False
            for min_param_set in minimum_list:
                if(min_param_set <= input_children_keys):
                    min_param_exist_flag = True
            if(not min_param_exist_flag):
                _error_at_least_one(mode, minimum_list, top_key)

    if(mode == 'normal'):
        format = normal_format
    elif(mode == 'chain'):
        format = chain_format
    input_top_keys = conf.keys()

    # Check 'Requirement' meets
    top_comp_keys = [k for k, v in format.items() if v['Requirement'] == 'compulsory']
    for top_comp_key in top_comp_keys:
        if(top_comp_key not in input_top_keys):
            _error_not_specified(mode, top_comp_key)
        if(format[top_comp_key]['Children']):
            __check_children_requirements(top_comp_key)

    input_top_opt_keys = set(input_top_keys) - set(top_comp_keys)
    for input_top_opt_key in input_top_opt_keys:
        if(format[input_top_opt_key]['Children']):
            __check_children_requirements(input_top_opt_key)

    # Check 'default' parameters
    top_default_keys = [k for k, v in format.items() if v['Requirement'] == 'default']
    for top_default_key in top_default_keys:
        default_list = [(k, v['Default']) for k, v in format[top_default_key]['Children'].items()
                                        if v['Requirement'] == 'default']
        default_child_k, default_child_v = default_list[0]  # HACK
        if(top_default_key not in input_top_keys or not conf[top_default_key]):
            conf[top_default_key] = {default_child_k: default_child_v}
            _warn_use_default(top_default_key, default_child_k)
        elif(True not in conf[top_default_key].values()):
            conf[top_default_key][default_child_k] = True
            _warn_use_default(top_default_key, default_child_k)

    # Check type correctness
    for input_top_key in input_top_keys:
        if(format_children := format[input_top_key]['Children']):
            for input_child_k, input_child_v in conf[input_top_key].items():
                correct_type = format_children[input_child_k]['Type']
                if(not _is_correct_type(input_child_v, correct_type)):
                    _error_invalid_type(mode, input_child_k, correct_type, input_top_key)
        else:
            correct_type = format[input_top_key]['Type']
            if(not _is_correct_type(conf[input_top_key], correct_type)):
                _error_invalid_type(mode, input_top_key, correct_type)


def _error_increase_or_decrease(increase_param: List[str]=[], decrease_param: List[str]=[]) -> None:
    if(len(increase_param) == 1):
        increase_str = f"'{increase_param[0]}'"
    elif(len(increase_param) >= 2):
        increase_str = ""
        for i, v in enumerate(increase_param):
            if(i == len(increase_param)-1):
                increase_str += f"'{v}'"
            else:
                increase_str += f"'{v}' or "

    if(len(decrease_param) == 1):
        decrease_str = f"'{decrease_param[0]}'"
    elif(len(decrease_param) >= 2):
        decrease_str = ""
        for i, v in enumerate(decrease_param):
            if(i == len(decrease_param)-1):
                decrease_str += f"'{v}'"
            else:
                decrease_str += f"'{v}' or "

    if(increase_param and decrease_param):
        print(f"[Error] Please increase {increase_str} or decrease {decrease_str}.")
    elif(increase_param):
        print(f"[Error] Please increase {increase_str}.")
    elif(decrease_param):
        print(f"[Error] Please decrease {decrease_str}.")
    exit(1)


def load_normal_config(config_yaml_file) -> Dict:
    conf = _load_yaml(config_yaml_file)
    _check_config_format('normal', conf)

    # Check 'In-degree' and 'Out-degree' feasibility
    if(conf['In-degree']['Max'] < conf['Out-degree']['Min']):
        _error_increase_or_decrease(['In-degree: Max'], ['Out-degree: Min'])
    if(conf['Out-degree']['Max'] < conf['In-degree']['Min']):
        _error_increase_or_decrease(['Out-degree: Max'], ['In-degree: Min'])

    # Check 'Max number of same-depth nodes' feasibility
    if('Max number of same-depth nodes' in conf.keys()):
        min_same_depth_num = max(conf['Out-degree']['Min'],
                                 int(np.ceil(
                                     conf['Number of entry nodes']*conf['Out-degree']['Min']
                                     / conf['In-degree']['Max'])))
        if(conf['Max number of same-depth nodes'] < min_same_depth_num):
            _error_increase_or_decrease(['Max number of same-depth nodes'])

    return conf


def load_chain_config(config_yaml_file) -> Dict:
    conf = _load_yaml(config_yaml_file)
    _check_config_format('chain', conf)
    
    # Check 'Number of nodes' feasibility
    if((conf['Number of chains']
                *(conf['Chain length']['Max']*conf['Chain width']['Max'] - conf['Chain width']['Max'] + 1))
                < conf['Number of nodes']):
        _error_increase_or_decrease(['Chain length: Max', 'Chain width: Max'], ['Number of nodes'])
    if((conf['Number of chains']
                *(conf['Chain length']['Min'] + conf['Chain width']['Min'] - 1))
                > conf['Number of nodes']):
        _error_increase_or_decrease(['Number of nodes'], ['Chain length: Max', 'Chain width: Max'])

    # Check 'Vertically link chains' feasibility
    if('Vertically link chains' in conf.keys()):
        max_num_chains = (conf['Vertically link chains']['Max level of vertical links']
                          * conf['Vertically link chains']['Max number of parallel chains'])
        if(conf['Number of chains'] > max_num_chains):
            print("[Error] Please increase 'Vertically link chains: Max level of vertical links' \
                   or 'Vertically link chains: Max number of parallel chains' \
                   or decrease 'Number of chains'.")
            exit(1)
        if('Number of entry nodes' in conf.keys() and conf['Number of entry nodes']
                > conf['Vertically link chains']['Max number of parallel chains']):
            print("[Error] Please increase 'Vertically link chains: Max level of vertical links' \
                   or 'Vertically link chains: Max number of parallel chains' \
                   or decrease 'Number of chains'.")
            exit(1)

    return conf
