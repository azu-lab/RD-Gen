import argparse
import os
import random
from logging import getLogger

import yaml

from src.builder.dag_builder_factory import DAGBuilder
from src.combo_generator import ComboGenerator
from src.config_loader import ConfigLoader
from src.dag_exporter import DAGExporter
from src.exceptions import MaxBuildFailError
from src.property_setter.property_setter import PropertySetter

logger = getLogger(__name__)


def option_parser():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config_path",
                            required=True,
                            type=str,
                            help="path of config file (.yaml)")
    arg_parser.add_argument("--dest_dir",
                            required=True,
                            type=str,
                            help="path of destination directory")
    args = arg_parser.parse_args()

    return args.config_path, args.dest_dir


def main(config_path, dest_dir):
    config_loader = ConfigLoader(config_path)
    combo_cfg = config_loader.load()
    random.seed(combo_cfg.get_value(["seed"]))
    combo_generator = ComboGenerator(combo_cfg)
    combo_iter = combo_generator.generate()

    for dir_name, log, cfg in combo_iter:
        combo_dest_dir = dest_dir + f'/{dir_name}'
        os.mkdir(combo_dest_dir)
        with open(f'{combo_dest_dir}/combination_log.yaml', 'w') as f:
            yaml.dump(log, f)

        # Generate DAG iterator
        generation_method = cfg.get_value(["GM"])
        if generation_method == "fan-in/fan-out":
            dag_builder = DAGBuilder.create_fan_in_fan_out_builder(cfg)
        elif generation_method == "fayer by layer":
            dag_builder = DAGBuilder.create_layer_by_layer_builder(cfg)
        elif generation_method == "chain-based":
            pass  # TODO
        else:
            raise NotImplementedError
        dag_raw_iter = dag_builder.build()

        # Set properties & Output
        property_setter = PropertySetter(cfg)
        dag_exporter = DAGExporter(cfg)
        try:
            for i, dag_raw in enumerate(dag_raw_iter):
                property_setter.set(dag_raw)
                dag_exporter.export(combo_dest_dir, f"dag_{i}", dag_raw)
        except MaxBuildFailError as e:
            logger.warning(e.message)


if __name__ == "__main__":
    config_path, dest_dir = option_parser()
    main(config_path, dest_dir)
