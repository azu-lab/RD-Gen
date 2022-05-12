import argparse
import os
import random
from logging import getLogger

import yaml

from src.builder.dag_builder_factory import DAGBuilder
from src.combo_generator import ComboGenerator
from src.config_format.format import Format
from src.config_loader import ConfigLoader
from src.exceptions import InvalidConfigError

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
    generation_method = cfg_raw["Generation method"]
    random.seed(cfg_raw['Seed'])
    format = Format(generation_method)
    config_loader = ConfigLoader(format, cfg_raw)
    combo_cfg = config_loader.load()
    combo_generator = ComboGenerator(combo_cfg)
    combo_iter = combo_generator.generate()

    for dir_name, log, cfg in combo_iter:
        combo_dest_dir = dest_dir + f'/{dir_name}'
        os.mkdir(combo_dest_dir)
        with open(f'{combo_dest_dir}/combination_log.yaml', 'w') as f:
            yaml.dump(log, f)

        try:
            # Build DAG
            if generation_method == "fan-in fan-out":
                dag_builder = DAGBuilder.create_fan_in_fan_out_builder(cfg)
            elif generation_method == "layer by layer":
                dag_builder = DAGBuilder.create_layer_by_layer_builder(cfg)
            elif generation_method == "chain-based":
                pass  # TODO
            else:
                raise NotImplementedError
            dag_raw = dag_builder.build()

        except InvalidConfigError as e:
            logger.warning(e.message)


if __name__ == "__main__":
    config_file, dest_dir = option_parser()
    main(config_file, dest_dir)
