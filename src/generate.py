import argparse
from logging import getLogger

import yaml

from src.combo_generator import ComboGenerator
from src.config_loader import ConfigLoader
from src.format import Format

logger = getLogger(__name__)


def option_parser():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config_path",
                            dest="config_file",
                            required=True,
                            type=argparse.FileType("r"),
                            help="path of config file (.yaml)")
    arg_parser.add_argument("--dest_dir",
                            required=True,
                            type=str,
                            help="path of destination directory")
    args = arg_parser.parse_args()

    return args.config_file, args.dest_dir


def main(config_file, dest_dir):
    cfg_raw = yaml.safe_load(config_file)
    format = Format(cfg_raw["Generation method"])
    config_loader = ConfigLoader(format, cfg_raw)
    combo_cfg = config_loader.load()
    combo_generator = ComboGenerator(combo_cfg)
    combo_iter = combo_generator.generate()
    for dir_name, log, cfg in combo_iter:
        pass  # TODO


if __name__ == "__main__":
    config_file, dest_dir = option_parser()
    main(config_file, dest_dir)
