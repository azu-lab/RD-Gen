import argparse
import file_handling_helper
from typing import Union


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


def main(config_yaml_file, dest_dir):
    config = file_handling_helper.load_config(config_yaml_file)
    print('TODO: 処理を書く')


if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    main(config_yaml_file, dest_dir)