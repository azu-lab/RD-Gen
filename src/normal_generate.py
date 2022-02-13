import argparse
import file_handling_helper
from typing import Union, Dict, List


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


def error_show_normal_config_format() -> None:
    print('\n')
    print('Please describe the configuration file as follows:')
    print('--------------------------------------------------')
    print('# Compulsory parameters')
    print('Number of DAGs: <int>')
    print('Initial seed: <int>')
    print('Initial node index: <int>')
    print('Number of nodes: <int>')
    print('Number of entry nodes: <int>')
    print('Number of exit nodes: <int>')
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
    config = file_handling_helper.load_config(config_yaml_file)
    
    compulsory_params = ['Number of DAGs',
                         'Initial seed',
                         'Initial node index',
                         'Number of nodes',
                         'Number of entry nodes',
                         'Number of exit nodes',
                         'In-degree',
                         'Out-degree',
                         'Execution time']
    
    # check compulsory parameter exists
    try:
        for compulsory_param in compulsory_params:
            config[compulsory_param]
    except KeyError:
        print(f"Compulsory parameter '{compulsory_param}' is not specified.")
        error_show_normal_config_format()
    
    # check format
    for input_param in config.keys():
        if(input_param in ['In-degree', 'Out-degree']):  # 'Min' and 'Max'
            if(isinstance(config[input_param]['Min'], int) == False or
                    isinstance(config[input_param]['Max'], int) == False):
                print("Type of 'Min' and 'Max' must be <int>.")
                error_show_normal_config_format()
                
        elif(input_param in ['Execution time', 'Use communication time']):  # 'Min', 'Max', and 'Use list'
            if('Use list' in config[input_param].keys()):
                if(check_list_int(config[input_param]['Use list']) == False):
                    print("Type of 'Use list' values must be <int>.")
                    error_show_normal_config_format()
            else:
                if(isinstance(config[input_param]['Min'], int) == False or
                        isinstance(config[input_param]['Max'], int) == False):
                    print("Type of 'Min' and 'Max' must be <int>.")
                    error_show_normal_config_format()
        
        elif(input_param == 'Use multi-period'):
            try:
                periodic_type = config[input_param]['Periodic type']
                if(periodic_type not in ['All', 'Entry', 'Random']):
                    print(f"'Periodic type' must be 'All', 'Entry', or 'Random'.")
                    error_show_normal_config_format()
            except KeyError:
                print(f"'Periodic type' is not specified.")
                error_show_normal_config_format()
            
            try:
                if(isinstance(config[input_param]['Descendants have smaller period'], bool) == False):
                    print("Type of 'Descendants have smaller period' must be <bool>.")
                    error_show_normal_config_format()
            except KeyError:
                print(f"'Descendants have smaller period' is not specified.")
                error_show_normal_config_format()
            
            if('Use list' in config[input_param].keys()):
                if(check_list_int(config[input_param]['Use list']) == False):
                    print("Type of 'Use list' values must be <int>.")
                    error_show_normal_config_format()
            else:
                if(isinstance(config[input_param]['Min'], int) == False or
                        isinstance(config[input_param]['Max'], int) == False):
                    print("Type of 'Min' and 'Max' must be <int>.")
                    error_show_normal_config_format()
        else:
            if(isinstance(config[input_param], int) == False):
                print(f"Type of '{input_param}' must be <int>.")
                error_show_normal_config_format()

    return config


def main(config_yaml_file, dest_dir):
    config = load_normal_config(config_yaml_file)
    print('TODO: 処理を書く')


if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    main(config_yaml_file, dest_dir)