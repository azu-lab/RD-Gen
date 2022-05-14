

# def option_parser() -> Tuple[argparse.FileType, str]:
#     usage = f'[python] {__file__} \
#               --config_yaml_path [<path to config file>] \
#               --dest_dir [<destination directory>]'

#     arg_parser = argparse.ArgumentParser(usage=usage)
#     arg_parser.add_argument('--config_yaml_path',
#                             type=argparse.FileType(("r")),
#                             help='config file name (.yaml)')
#     arg_parser.add_argument('--dest_dir',
#                             type=str,
#                             default='./',
#                             help='destination directory')
#     args = arg_parser.parse_args()

#     return args.config_yaml_path, args.dest_dir


# def choice_one_from_cfg(param_cfg: dict) -> Union[int, float]:
#     if('Random' in param_cfg.keys()):
#         return random.choice(param_cfg['Random'])
#     elif('Fixed' in param_cfg.keys()):
#         return param_cfg['Fixed']


# def get_cp(dag: nx.DiGraph, source, exit) -> Tuple[List[int], int]:
#     cp = []
#     cp_len = 0

#     paths = nx.all_simple_paths(dag, source=source, target=exit)
#     for path in paths:
#         path_len = 0
#         for i in range(len(path)):
#             path_len += dag.nodes[path[i]]['exec']
#             if(i != len(path)-1 and
#                     'comm' in list(dag.edges[path[i], path[i+1]].keys())):
#                 path_len += dag.edges[path[i], path[i+1]]['comm']
#         if(path_len > cp_len):
#             cp = path
#             cp_len = path_len

#     return cp, cp_len


# def random_set_e2e_deadline(cfg, G: nx.DiGraph) -> None:
#     if(TO_ORI['UMP'] in cfg.keys() and
#             TO_ORI['RDP'] in cfg[TO_ORI['UED']].keys()):
#         max_period = max((nx.get_node_attributes(G, 'period')).values())
#         for exit_i in [v for v, d in G.out_degree() if d == 0]:
#             G.nodes[exit_i]['deadline'] = \
#                 int(max_period *
#                     choice_one_from_cfg(cfg[TO_ORI['UED']][TO_ORI['RDP']]))

#     elif(TO_ORI['RDC'] in cfg[TO_ORI['UED']].keys()):
#         for exit_i in [v for v, d in G.out_degree() if d == 0]:
#             max_cp_len = 0
#             for entry_i in [v for v, d in G.in_degree() if d == 0]:
#                 _, cp_len = get_cp(G, entry_i, exit_i)
#                 if(cp_len > max_cp_len):
#                     max_cp_len = cp_len
#             G.nodes[exit_i]['deadline'] = \
#                 int(max_cp_len *
#                     choice_one_from_cfg(cfg[TO_ORI['UED']][TO_ORI['RDC']]))


# def get_min_of_range(param_cfg: Dict) -> Union[float, int]:
#     if('Random' in param_cfg.keys()):
#         return min(param_cfg['Random'])
#     elif('Fixed' in param_cfg.keys()):
#         return param_cfg['Fixed']


# def get_max_of_range(param_cfg: Dict) -> Union[float, int]:
#     if('Random' in param_cfg.keys()):
#         return max(param_cfg['Random'])
#     elif('Fixed' in param_cfg.keys()):
#         return param_cfg['Fixed']
