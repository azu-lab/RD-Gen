import os
import sys
import yaml


def load_config(config_yaml_file):
    try:
        config = yaml.safe_load(config_yaml_file)
    except yaml.YAMLError:
        print(f"error when loading yaml: {sys.exc_info()}", file=sys.stderr)
        exit(1)

    return config