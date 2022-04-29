import networkx as nx
import numpy as np
import random
import copy
from typing import List, Tuple

from src.chain import Chain
from src.utils import get_settable_min_exec, get_settable_min_comm, get_settable_max_period
# from file_handling_helper import _error_increase_or_decrease


def _random_get_period(node_i, conf, dag: nx.DiGraph, chain: Chain=None) -> Tuple[bool, int]:
    # Determine lower_bound
    if(conf['Use multi-period']['Periodic type'] == 'Chain'):
        lower_bound = np.ceil(chain.get_sum_cost(conf, dag)
                          / conf['Use multi-period']['Max ratio of execution time to period'])
    else:
        lower_bound = np.ceil(dag.nodes[node_i]['exec']
                            / conf['Use multi-period']['Max ratio of execution time to period'])

    if('Descendants have larger period' in conf['Use multi-period'].keys() and
            conf['Use multi-period']['Descendants have larger period']):
        ancestors = list(nx.ancestors(dag, node_i))
        anc_periods = []
        for ancestor in ancestors:
            if 'period' in list(dag.nodes[ancestor].keys()):
                anc_periods.append(dag.nodes[ancestor]['period'])
        if(anc_periods):
            lower_bound = max(max(anc_periods), lower_bound)

    # Choice period
    try:
        if('Use list' in conf['Use multi-period'].keys()):
            period_options = [t for t in conf['Use multi-period']['Use list']
                            if t >= lower_bound]
            return True, random.choice(period_options)
        else:
            return True, random.randint(lower_bound, conf['Use multi-period']['Max'])
    except (IndexError, ValueError):
        return False, None


def _set_period_all(conf, G: nx.DiGraph) -> None:
    for node_i in G.nodes():
        result, value = _random_get_period(node_i, conf, G)
        if(result):
            G.nodes[node_i]['period'] = value
        else:
            pass  # TODO


def _set_period_entry(conf, G: nx.DiGraph) -> None:
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
            result, value = _random_get_period(entry_i, conf, G)
            if(result):
                G.nodes[entry_i]['period'] = value
            else:
                pass  # TODO


def _set_period_exit(conf, G: nx.DiGraph) -> None:
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
            result, value = _random_get_period(exit_i, conf, G)
            if(result):
                G.nodes[exit_i]['period'] = value
            else:
                pass  # TODO


def _set_period_chain(conf, G: nx.DiGraph, chains: List[Chain]) -> None:
    for chain in chains:
        result, value = _random_get_period(chain.head, conf, G, chain)
        if(result):
            G.nodes[chain.head]['period'] = value
        else:
            # Check feasibility
            if('Use communication time' in conf.keys()):
                min_sum_cost = (get_settable_min_exec(conf)*len(chain.nodes)
                                + get_settable_min_comm(conf)*len(chain.get_edges(G)))
            else:
                min_sum_cost = get_settable_min_exec(conf)*len(chain.nodes)
            min_lower_bound = np.ceil(min_sum_cost
                          / conf['Use multi-period']['Max ratio of execution time to period'])
            if(min_lower_bound > get_settable_max_period(conf)):
                _error_increase_or_decrease(['Use multi-period: Max', 'Use multi-period: Max ratio of execution time to period'],
                                            ['Execution time: Min', 'Use communication time: Min'])

            # Decrease sum cost of the chain
            else:
                decrease_vol = int(np.ceil(chain.get_sum_cost(conf, G)
                                           / conf['Use multi-period']['Max ratio of execution time to period']
                                           - get_settable_max_period(conf)))
                goal_sum_cost = chain.get_sum_cost(conf, G) - decrease_vol
                decrease_options = chain.nodes
                if('Use communication time' in conf.keys()):
                    decrease_options += chain.get_edges(G)

                while(chain.get_sum_cost(conf, G) > goal_sum_cost and decrease_options):
                    choose = random.choice(decrease_options)
                    if(isinstance(choose, tuple)):
                        s, t = choose
                        if(G.edges[s, t]['comm'] == get_settable_min_comm(conf)):
                            decrease_options.remove(choose)
                        else:
                            if('Use list' in conf['Use communication time']):
                                sorted_comm = sorted(conf['Use communication time']['Use list'])
                                G.edges[s, t]['comm'] = sorted_comm[sorted_comm.index(G.edges[s, t]['comm']) - 1]
                            else:
                                G.edges[s, t]['comm'] -= 1
                    else:
                        if(G.nodes[choose]['exec'] == get_settable_min_exec(conf)):
                            decrease_options.remove(choose)
                        else:
                            if('Use list' in conf['Execution time']):
                                sorted_exec = sorted(conf['Execution time']['Use list'])
                                G.nodes[choose]['exec'] = sorted_exec[sorted_exec.index(G.nodes[choose]['exec']) - 1]
                            else:
                                G.nodes[choose]['exec'] -= 1

            # Set period
            result, value = _random_get_period(chain.head, conf, G, chain)
            G.nodes[chain.head]['period'] = value


def random_set_period(conf, G: nx.DiGraph, chains: List[Chain]=[]) -> None:
    if(conf['Use multi-period']['Periodic type'] == 'All'):
        _set_period_all(conf, G)
    elif(conf['Use multi-period']['Periodic type'] == 'Entry'):
        _set_period_entry(conf, G)
    elif(conf['Use multi-period']['Periodic type'] == 'Chain'):
        _set_period_chain(conf, G, chains)

    if('Entry node periods' in conf['Use multi-period'].keys()):
        _set_period_entry(conf, G)
    if('Exit node periods' in conf['Use multi-period'].keys()):
        _set_period_exit(conf, G)
