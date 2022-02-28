import os
import sys
import yaml
import numpy as np
from typing import Union, Dict, List


def _load_config(config_yaml_file):
    try:
        config = yaml.safe_load(config_yaml_file)
    except yaml.YAMLError:
        print(f"error when loading yaml: {sys.exc_info()}", file=sys.stderr)
        exit(1)

    return config


def _error_show_normal_config_format() -> None:
    print('\n')
    print('Please describe the configuration file as follows:')
    print('--------------------------------------------------')
    print('# Compulsory parameters')
    print('Number of DAGs: <int>')
    print('Initial seed: <int>')
    print('Number of nodes: <int>')
    print('Number of entry nodes: <int>')
    print('In-degree:')
    print('  Min: <int>')
    print('  Max: <int>')
    print('Out-degree:')
    print('  Min: <int>')
    print('  Max: <int>')
    print('Execution time:')
    print('  Min: <int>')
    print('  Max: <int>')
    print('  Use list: [<int>, ..., <int>]  # (optional)')
    print('\n')
    print('# Optional parameters')
    print('Force merge to exit nodes:')
    print('  Number of exit nodes: <int>')
    print('Use communication time:')
    print('  Min: <int>')
    print('  Max: <int>')
    print('  Use list: [<int>, ..., <int>]  # (optional)')
    print('Use multi-period:')
    print("  Periodic type: 'All' or 'Entry'")
    print('  Descendants have larger period: <bool>')
    print('  Max ratio of execution time to period: <float>')
    print('  Min: <int>')
    print('  Max: <int>')
    print('  Use list: [<int>, ..., <int>]  # (optional)')
    print('--------------------------------------------------\n')
    exit(1)


def _check_list_int(list : List) -> bool:
    for value in list:
        if(isinstance(value, int) == False):
            return False
    
    return True


def load_normal_config(config_yaml_file) -> Dict:
    config = _load_config(config_yaml_file)
    
    compulsory_params = ['Number of DAGs',
                         'Initial seed',
                         'Number of nodes',
                         'Number of entry nodes',
                         'In-degree',
                         'Out-degree',
                         'Execution time']
    
    # check compulsory parameter exists
    try:
        for compulsory_param in compulsory_params:
            config[compulsory_param]
    except KeyError:
        print(f"[Error] Compulsory parameter '{compulsory_param}' is not specified.")
        _error_show_normal_config_format()
    
    # check format
    for input_param in config.keys():
        if(input_param in ['In-degree', 'Out-degree']):  # 'Min' and 'Max'
            if(isinstance(config[input_param]['Min'], int) == False or
                    isinstance(config[input_param]['Max'], int) == False):
                print("[Error] Type of 'Min' and 'Max' must be <int>.")
                _error_show_normal_config_format()
                
        elif(input_param in ['Execution time', 'Use communication time']):  # 'Min', 'Max', and 'Use list'
            if('Use list' in config[input_param].keys()):
                if(_check_list_int(config[input_param]['Use list']) == False):
                    print("[Error] Type of 'Use list' values must be <int>.")
                    _error_show_normal_config_format()
            else:
                if(isinstance(config[input_param]['Min'], int) == False or
                        isinstance(config[input_param]['Max'], int) == False):
                    print("[Error] Type of 'Min' and 'Max' must be <int>.")
                    _error_show_normal_config_format()
        
        elif(input_param == 'Force merge to exit nodes'):
            try:
                if(isinstance(config[input_param]['Number of exit nodes'], int) == False):
                    print("[Error] Type of 'Number of exit nodes' must be <int>.")
                    _error_show_normal_config_format()
            except KeyError:
                print(f"'[Error] Number of exit nodes' is not specified.")
                _error_show_normal_config_format()
        
        elif(input_param == 'Use multi-period'):
            try:
                periodic_type = config[input_param]['Periodic type']
                if(periodic_type not in ['All', 'Entry']):
                    print(f"[Error] 'Periodic type' must be 'All' or 'Entry'.")
                    _error_show_normal_config_format()
            except KeyError:
                print(f"[Error] 'Periodic type' is not specified.")
                _error_show_normal_config_format()
            
            try:
                if(isinstance(config[input_param]['Descendants have larger period'], bool) == False):
                    print("[Error] Type of 'Descendants have larger period' must be <bool>.")
                    _error_show_normal_config_format()
            except KeyError:
                print(f"[Error] 'Descendants have larger period' is not specified.")
                _error_show_normal_config_format()
            
            try:
                if(isinstance(config[input_param]['Max ratio of execution time to period'], float) == False):
                    print("[Error] Type of 'Max ratio of execution time to period' must be <float>.")
                    _error_show_normal_config_format()
            except KeyError:
                print(f"[Error] 'Max ratio of execution time to period' is not specified.")
                _error_show_normal_config_format()
            
            if('Use list' in config[input_param].keys()):
                if(_check_list_int(config[input_param]['Use list']) == False):
                    print("[Error] Type of 'Use list' values must be <int>.")
                    _error_show_normal_config_format()
            else:
                if(isinstance(config[input_param]['Min'], int) == False or
                        isinstance(config[input_param]['Max'], int) == False):
                    print("[Error] Type of 'Min' and 'Max' must be <int>.")
                    _error_show_normal_config_format()
        else:
            if(isinstance(config[input_param], int) == False):
                print(f"[Error] Type of '{input_param}' must be <int>.")
                _error_show_normal_config_format()
    
    # Validation check of In-degree and Out-degree
    if(config['In-degree']['Max'] < config['Out-degree']['Min']):
        print("[Error] Please increase 'Max' of 'In-degree' or decrease 'Min' of 'Out-degree'.")
        exit(1)
    if(config['Out-degree']['Max'] < config['In-degree']['Min']):
        print("[Error] Please increase 'Max' of 'Out-degree' or decrease 'Min' of 'In-degree'.")
        exit(1)
    
    # Check 'Max ratio of execution time to period' feasibility
    if('Use multi-period' in config.keys()):
        max_exec_time = None
        if('Use list' in config['Execution time'].keys()):
            max_exec_time = max(config['Execution time']['Use list'])
        else:
            max_exec_time = config['Execution time']['Max']
        
        max_period = None
        if('Use list' in config['Use multi-period'].keys()):
            max_period = max(config['Use multi-period']['Use list'])
        else:
            max_period = config['Use multi-period']['Max']
        
        max_lower_bound = np.ceil(max_exec_time
                                    / config['Use multi-period']['Max ratio of execution time to period'])
        if(max_lower_bound > max_period):
            print("[Error] 'Max ratio of execution time to period' may not be satisfied. \
                  Please increase the maximum value of period or decrease the maximum value of execution time.")
            exit(1)
    
    # Check 'Max number of same-depth nodes' feasibility
    if('Max number of same-depth nodes' in config.keys()):
        min_same_depth_num = max(config['Out-degree']['Min'], 
                      int(np.ceil(config['Number of entry nodes']*config['Out-degree']['Min'] 
                                  / config['In-degree']['Max'])))

        if(config['Max number of same-depth nodes'] < min_same_depth_num):
            print("[Error] 'Max number of same-depth nodes' is too small. \
                  Please increase 'Max number of same-depth nodes'.")
            exit(1)

    return config