import numpy as np
import networkx as nx
import random
import copy
import yaml
import json
from typing import List, Tuple
from networkx.readwrite import json_graph

from utils import option_parser
from file_handling_helper import load_chain_config
from write_dag import write_dag
from random_set_period import random_set_period

def main(conf, dest_dir):
    pass  # TODO


if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    config = load_chain_config(config_yaml_file)
    main(config, dest_dir)
