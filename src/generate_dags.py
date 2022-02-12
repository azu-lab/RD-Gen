import argparse
from typing import Union


def option_parser() -> Union[bool, argparse.FileType]:
    usage = f'[python] {__file__} [<True|False>] --dest_dir [<destination directory>]'

    arg_parser = argparse.ArgumentParser(usage=usage)
    arg_parser.add_argument('--use_chain',
                            action='store_true',
                            help='chain-based generation')
    arg_parser.add_argument('--dest_dir',
                            type=str,
                            default='./',
                            help='destination directory')
    args = arg_parser.parse_args()

    return args.use_chain, args.dest_dir


def main(use_chain, dest_dir):
    print('TODO: 処理を書く')


if __name__ == '__main__':
    use_chain, dest_dir = option_parser()
    main(use_chain, dest_dir)