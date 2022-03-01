import networkx as nx
import numpy as np
import random


def _random_get_period(node_i, config, dag: nx.DiGraph) -> int:
    lower_bound = None

    # Determine lower_bound
    if(config['Use multi-period']['Periodic type'] == 'Chain'):
        # TODO
        pass
    else:
        lower_bound = np.ceil(dag.nodes[node_i]['execution_time']
                              / config['Use multi-period']['Max ratio of execution time to period'])

    if(config['Use multi-period']['Descendants have larger period']):
        ancestors = list(nx.ancestors(dag, node_i))
        anc_periods = []
        for ancestor in ancestors:
            if 'period' in list(dag.nodes[ancestor].keys()):
                anc_periods.append(dag.nodes[ancestor]['period'])
        if(anc_periods):
            lower_bound = max(max(anc_periods), lower_bound)

    # Choice period
    if('Use list' in config['Use multi-period'].keys()):
        period_options = [t for t in config['Use multi-period']['Use list']
                          if t >= lower_bound]
        return random.choice(period_options)
    else:
        return random.randint(lower_bound, config['Use multi-period']['Max'])


def _set_all(config, G):
    for node_i in G.nodes():
        G.nodes[node_i]['period'] = _random_get_period(node_i, config, G)


def _set_entry(config, G):
    entry_nodes = [v for v, d in G.in_degree() if d == 0]
    for entry_i in entry_nodes:
        G.nodes[entry_i]['period'] = _random_get_period(entry_i, config, G)


def _set_chain(config, G):
    # TODO
    pass


def random_set_period(config, mode: str, G: nx.DiGraph) -> None:
    if(mode not in ['normal', 'chain']):
        print('[Error] Invalid mode name was specified.')
        exit(1)

    if(config['Use multi-period']['Periodic type'] == 'All'):
        _set_all(config, G)
    elif(config['Use multi-period']['Periodic type'] == 'Entry'):
        _set_entry(config, G)

    if(mode == 'chain' and
            config['Use multi-period']['Periodic type'] == 'Chain'):
        _set_chain(config, G)
