import networkx as nx
import numpy as np
import random
import copy


def _random_get_period(node_i, conf, dag: nx.DiGraph) -> int:
    lower_bound = None

    # Determine lower_bound
    if(conf['Use multi-period']['Periodic type'] == 'Chain'):
        # TODO
        pass
    else:
        lower_bound = np.ceil(dag.nodes[node_i]['execution_time']
                              / conf['Use multi-period']['Max ratio of execution time to period'])

    if(conf['Use multi-period']['Descendants have larger period']):
        ancestors = list(nx.ancestors(dag, node_i))
        anc_periods = []
        for ancestor in ancestors:
            if 'period' in list(dag.nodes[ancestor].keys()):
                anc_periods.append(dag.nodes[ancestor]['period'])
        if(anc_periods):
            lower_bound = max(max(anc_periods), lower_bound)

    # Choice period
    if('Use list' in conf['Use multi-period'].keys()):
        period_options = [t for t in conf['Use multi-period']['Use list']
                          if t >= lower_bound]
        return random.choice(period_options)
    else:
        return random.randint(lower_bound, conf['Use multi-period']['Max'])


def _set_all(conf, G: nx.DiGraph) -> None:
    for node_i in G.nodes():
        G.nodes[node_i]['period'] = _random_get_period(node_i, conf, G)
    
    if('Entry node periods' in conf['Use multi-period'].keys()):
        _set_entry(conf, G)
    if('Exit node periods' in conf['Use multi-period'].keys()):
        _set_exit(conf, G)


def _set_entry(conf, G: nx.DiGraph) -> None:
    entry_nodes = [v for v, d in G.in_degree() if d == 0]
    if('Entry node periods' in conf['Use multi-period'].keys()):
        unused_entry_periods = copy.deepcopy(conf['Use multi-period']['Entry node periods'])
        for entry_i in entry_nodes:
            if(not unused_entry_periods):
                unused_entry_periods = copy.deepcopy(conf['Use multi-period']['Entry node periods'])
            choose_period = random.choice(unused_entry_periods)
            G.nodes[entry_i]['period'] = choose_period
            unused_entry_periods.remove(choose_period)
    else:
        for entry_i in entry_nodes:
            G.nodes[entry_i]['period'] = _random_get_period(entry_i, conf, G)


def _set_exit(conf, G: nx.DiGraph) -> None:
    exit_nodes = [v for v, d in G.out_degree() if d == 0]
    if('Exit node periods' in conf['Use multi-period'].keys()):
        unused_exit_periods = copy.deepcopy(conf['Use multi-period']['Exit node periods'])
        for exit_i in exit_nodes:
            if(not unused_exit_periods):
                unused_exit_periods = copy.deepcopy(conf['Use multi-period']['Exit node periods'])
            choose_period = random.choice(unused_exit_periods)
            G.nodes[exit_i]['period'] = choose_period
            unused_exit_periods.remove(choose_period)
    else:
        for exit_i in exit_nodes:
            G.nodes[exit_i]['period'] = _random_get_period(exit_i, conf, G)


def _set_chain(conf, G):
    # TODO
    pass


def random_set_period(conf, G: nx.DiGraph) -> None:
    if(conf['Use multi-period']['Periodic type'] == 'All'):
        _set_all(conf, G)
    elif(conf['Use multi-period']['Periodic type'] == 'Entry'):
        _set_entry(conf, G)
    elif(conf['Use multi-period']['Periodic type'] == 'Chain'):
        _set_chain(conf, G)
