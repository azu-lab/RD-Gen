import os
import sys
import yaml
from typing import Union, Dict, List


def load_config(config_yaml_file):
    try:
        config = yaml.safe_load(config_yaml_file)
    except yaml.YAMLError:
        print(f"error when loading yaml: {sys.exc_info()}", file=sys.stderr)
        exit(1)

    return config


def error_show_normal_config_format() -> None:
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
    print("  Periodic type: 'All', 'Entry' or 'Random'")
    print('  Descendants have smaller period: <bool>')
    print('  Min: <int>')
    print('  Max: <int>')
    print('  Use list: [<int>, ..., <int>]  # (optional)')
    print('--------------------------------------------------\n')
    exit(1)


def check_list_int(list : List) -> bool:
    for value in list:
        if(isinstance(value, int) == False):
            return False
    
    return True


def load_normal_config(config_yaml_file) -> Dict:
    config = load_config(config_yaml_file)
    
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
        error_show_normal_config_format()
    
    # check format
    for input_param in config.keys():
        if(input_param in ['In-degree', 'Out-degree']):  # 'Min' and 'Max'
            if(isinstance(config[input_param]['Min'], int) == False or
                    isinstance(config[input_param]['Max'], int) == False):
                print("[Error] Type of 'Min' and 'Max' must be <int>.")
                error_show_normal_config_format()
                
        elif(input_param in ['Execution time', 'Use communication time']):  # 'Min', 'Max', and 'Use list'
            if('Use list' in config[input_param].keys()):
                if(check_list_int(config[input_param]['Use list']) == False):
                    print("[Error] Type of 'Use list' values must be <int>.")
                    error_show_normal_config_format()
            else:
                if(isinstance(config[input_param]['Min'], int) == False or
                        isinstance(config[input_param]['Max'], int) == False):
                    print("[Error] Type of 'Min' and 'Max' must be <int>.")
                    error_show_normal_config_format()
        
        elif(input_param == 'Force merge to exit nodes'):
            try:
                if(isinstance(config[input_param]['Number of exit nodes'], int) == False):
                    print("[Error] Type of 'Number of exit nodes' must be <int>.")
                    error_show_normal_config_format()
            except KeyError:
                print(f"'[Error] Number of exit nodes' is not specified.")
                error_show_normal_config_format()
        
        elif(input_param == 'Use multi-period'):
            try:
                periodic_type = config[input_param]['Periodic type']
                if(periodic_type not in ['All', 'Entry', 'Random']):
                    print(f"'[Error] Periodic type' must be 'All', 'Entry', or 'Random'.")
                    error_show_normal_config_format()
            except KeyError:
                print(f"'[Error] Periodic type' is not specified.")
                error_show_normal_config_format()
            
            try:
                if(isinstance(config[input_param]['Descendants have smaller period'], bool) == False):
                    print("[Error] Type of 'Descendants have smaller period' must be <bool>.")
                    error_show_normal_config_format()
            except KeyError:
                print(f"'[Error] Descendants have smaller period' is not specified.")
                error_show_normal_config_format()
            
            if('Use list' in config[input_param].keys()):
                if(check_list_int(config[input_param]['Use list']) == False):
                    print("[Error] Type of 'Use list' values must be <int>.")
                    error_show_normal_config_format()
            else:
                if(isinstance(config[input_param]['Min'], int) == False or
                        isinstance(config[input_param]['Max'], int) == False):
                    print("[Error] Type of 'Min' and 'Max' must be <int>.")
                    error_show_normal_config_format()
        else:
            if(isinstance(config[input_param], int) == False):
                print(f"[Error] Type of '{input_param}' must be <int>.")
                error_show_normal_config_format()
    
    # Validation check of In-degree and Out-degree
    if(config['In-degree']['Max'] < config['Out-degree']['Min']):
        print("[Error] Please increase 'Max' of 'In-degree' or decrease 'Min' of 'Out-degree'.")
        exit(1)
    if(config['Out-degree']['Max'] < config['In-degree']['Min']):
        print("[Error] Please increase 'Max' of 'Out-degree' or decrease 'Min' of 'In-degree'.")
        exit(1)


    return config