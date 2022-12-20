import argparse
import os
import shutil
import sys
from logging import getLogger
from typing import List

import yaml  # type: ignore
from tqdm import tqdm

from src import (
    BuildFailedError,
    ComboGenerator,
    ConfigValidator,
    DAGBuilderFactory,
    DAGExporter,
    PropertySetterBase,
    PropertySetterFactory,
)

logger = getLogger(__name__)


def main(config_path, dest_dir):
    with open(config_path) as f:
        config_raw = yaml.safe_load(f)

    # Validate config.
    ConfigValidator(config_raw).validate()

    # Generate combination.
    combo_gen = ComboGenerator(config_raw)
    combo_iter = combo_gen.get_combo_iter()
    num_combo = combo_gen.get_num_combos()

    # Loop for each combination.
    for dir_name, log, config in tqdm(combo_iter, total=num_combo, desc="Generated combinations"):
        combo_dest_dir = f"{dest_dir}/{dir_name}"
        os.mkdir(combo_dest_dir)
        with open(f"{combo_dest_dir}/combination_log.yaml", "w") as f:
            yaml.dump(log, f)

        dag_builder = DAGBuilderFactory().create_instance(config)
        dag_iter = dag_builder.build()

        # ---- Create all setters ----
        all_setter: List[PropertySetterBase] = []
        # Create setters for utilization, period, execution time and communication time.
        if config.multi_rate:
            all_setter.append(PropertySetterFactory.create_utilization_setter(config))
        elif config.ccr:
            all_setter.append(PropertySetterFactory.create_ccr_setter(config))
        if not all_setter:
            if config.execution_time:
                all_setter.append(
                    PropertySetterFactory.create_random_setter(config, "Execution time", "node")
                )
            if config.communication_time:
                all_setter.append(
                    PropertySetterFactory.create_random_setter(
                        config, "Communication time", "edge"
                    )
                )
        # Create setter for end-to-end deadline.
        if config.end_to_end_deadline:
            all_setter.append(PropertySetterFactory.create_deadline_setter(config))
        # Create setter for offset.
        if config.offset:
            all_setter.append(PropertySetterFactory.create_random_setter(config, "Offset", "node"))
        # Create setter for additional properties.
        if config.additional_properties:
            all_setter.append(PropertySetterFactory.create_additional_setter(config))

        dag_exporter = DAGExporter(config)
        # Loop for each dag.
        for i, dag in enumerate(dag_iter):
            try:
                # Set all properties.
                for setter in all_setter:
                    setter.set(dag)
                # Export DAG.
                dag_exporter.export(dag, combo_dest_dir, f"dag_{i}")
            except BuildFailedError as e:
                logger.warning(e.message)


def option_parser():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-c", "--config_path", required=True, type=str, help="path to config YAML file."
    )
    arg_parser.add_argument(
        "-d", "--dest_dir", required=True, type=str, help="path to destination directory."
    )
    args = arg_parser.parse_args()

    return args.config_path, args.dest_dir


if __name__ == "__main__":
    config_path, dest_dir = option_parser()

    # Check whether config_path exists.
    if not os.path.isfile(config_path):
        logger.error(f"{config_path} not found.")
        sys.exit(1)

    # Check whether dest_dir already exists.
    if os.path.isdir(dest_dir):
        logger.warning(
            "The following directory is already existing. Do you overwrite? "
            f"DIRECTORY: {dest_dir}"
        )
        yes = ["y", "yes"]
        no = ["n", "no"]
        while True:
            ans = input("[Y]es / [N]o?:").lower()
            if ans not in (yes + no):
                print("[Error] Input again [Y]es or [N]o.")
                continue
            break
        if ans in yes:
            # Overwrite directory.
            shutil.rmtree(dest_dir)
            os.mkdir(dest_dir)
        else:
            # Cancel generation.
            logger.info("Generation cancelled.")
            sys.exit(0)
    else:
        # Create destination directory.
        os.mkdir(dest_dir)

    # Start generation.
    main(config_path, dest_dir)
    logger.info("Generation successfully completed.")
