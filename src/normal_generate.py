import argparse
import file_handling_helper
from typing import Union, Dict
import networkx as nx
import random
from matplotlib import pyplot as plt


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


def random_get_exec_time(config : Dict) -> int:
    if('Use list' in config['Execution time'].keys()):
        return random.choice(config['Execution time']['Use list'])
    else:
        return random.randint(config['Execution time']['Min'], config['Execution time']['Max'])


def main(config, dest_dir):
    # Validation check of In-degree and Out-degree
    if(config['In-degree']['Max'] < config['Out-degree']['Min']):
        print("[Error] Please increase 'Max' of 'In-degree' or decrease 'Min' of 'Out-degree'.")
        exit(1)
    if(config['Out-degree']['Max'] < config['In-degree']['Min']):
        print("[Error] Please increase 'Max' of 'Out-degree' or decrease 'Min' of 'In-degree'.")
        exit(1)
    
    # Generarte DAGs
    for dag_i in range(config['Number of DAGs']):
        # Initialize variables
        random.seed(config['Initial seed'] + dag_i)
        node_i = config['Initial node index']
        G = nx.DiGraph()
        
        # Add entry nodes
        for i in range(config['Number of entry nodes']):
            G.add_node(node_i, execution_time=random_get_exec_time(config))
            node_i += 1
        
        nx.draw(G, pos=nx.planar_layout(G))
        plt.savefig('test.pdf')
        
        # TODO: 後続ノードがないノードに対して、子を生成する処理を繰り返す
        # while(G.number_of_nodes() == config['Number of nodes']):
        #     leaves = [v for v, d in G.out_degree() if d == 0]
        #     for leaf in leaves:
                
            
        
        # TODO: 強制マージなら exit node を追加し、後続ノードがないノードをすべて繋ぐ
        # TODO: 通信時間を使うなら、通信時間をランダムに決める
        # TODO: 最後に Periodic type に応じて、周期タスクにする
        # TODO: 描画（別関数）

if __name__ == '__main__':
    config_yaml_file, dest_dir = option_parser()
    config = file_handling_helper.load_normal_config(config_yaml_file)
    main(config, dest_dir)