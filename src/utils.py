import argparse
from typing import Tuple


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
