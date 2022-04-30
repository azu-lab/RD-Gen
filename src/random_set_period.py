import networkx as nx
import numpy as np
import random
import copy

from typing import List, Tuple

from src.chain import Chain
from src.utils import get_settable_min_exec, get_settable_min_comm, get_settable_max_period
from src.abbreviation import ToO, ToA
from src.exceptions import NoSettablePeriodError


# def _set_period_chain(conf, G: nx.DiGraph, chains: List[Chain]) -> None:
#     for chain in chains:
#         result, value = _random_get_period(chain.head, conf, G, chain)
#         if(result):
#             G.nodes[chain.head]['period'] = value
#         else:
#             # Check feasibility
#             if('Use communication time' in conf.keys()):
#                 min_sum_cost = (get_settable_min_exec(conf)*len(chain.nodes)
#                                 + get_settable_min_comm(conf)*len(chain.get_edges(G)))
#             else:
#                 min_sum_cost = get_settable_min_exec(conf)*len(chain.nodes)
#             min_lower_bound = np.ceil(min_sum_cost
#                           / conf['Use multi-period']['Max ratio of execution time to period'])
#             if(min_lower_bound > get_settable_max_period(conf)):
#                 _error_increase_or_decrease(['Use multi-period: Max', 'Use multi-period: Max ratio of execution time to period'],
#                                             ['Execution time: Min', 'Use communication time: Min'])

#             # Decrease sum cost of the chain
#             else:
#                 decrease_vol = int(np.ceil(chain.get_sum_cost(conf, G)
#                                            / conf['Use multi-period']['Max ratio of execution time to period']
#                                            - get_settable_max_period(conf)))
#                 goal_sum_cost = chain.get_sum_cost(conf, G) - decrease_vol
#                 decrease_options = chain.nodes
#                 if('Use communication time' in conf.keys()):
#                     decrease_options += chain.get_edges(G)

#                 while(chain.get_sum_cost(conf, G) > goal_sum_cost and decrease_options):
#                     choose = random.choice(decrease_options)
#                     if(isinstance(choose, tuple)):
#                         s, t = choose
#                         if(G.edges[s, t]['comm'] == get_settable_min_comm(conf)):
#                             decrease_options.remove(choose)
#                         else:
#                             if('Use list' in conf['Use communication time']):
#                                 sorted_comm = sorted(conf['Use communication time']['Use list'])
#                                 G.edges[s, t]['comm'] = sorted_comm[sorted_comm.index(G.edges[s, t]['comm']) - 1]
#                             else:
#                                 G.edges[s, t]['comm'] -= 1
#                     else:
#                         if(G.nodes[choose]['exec'] == get_settable_min_exec(conf)):
#                             decrease_options.remove(choose)
#                         else:
#                             if('Use list' in conf['Execution time']):
#                                 sorted_exec = sorted(conf['Execution time']['Use list'])
#                                 G.nodes[choose]['exec'] = sorted_exec[sorted_exec.index(G.nodes[choose]['exec']) - 1]
#                             else:
#                                 G.nodes[choose]['exec'] -= 1

#             # Set period
#             result, value = _random_get_period(chain.head, conf, G, chain)
#             G.nodes[chain.head]['period'] = value


def random_set_period(cfg, G: nx.DiGraph, chains: List[Chain]=[]) -> None:
    def random_get_period(
        node_i: int,
        cfg,
        dag: nx.DiGraph,
        chain: Chain=None
    ) -> int:
        if('Fixed' in cfg[ToO['UMP']][ToO['P']].keys()):
            return cfg[ToO['UMP']][ToO['P']]['Fixed']
        
        ### Determine lower_bound
        lower_bound = None
        # if(cfg['Use multi-period']['Periodic type'] == 'Chain'):
        #     lower_bound = np.ceil(chain.get_sum_cost(cfg, dag)
        #                     / cfg['Use multi-period']['Max ratio of execution time to period'])
        # else:
        #     lower_bound = np.ceil(dag.nodes[node_i]['exec']
        #                         / cfg['Use multi-period']['Max ratio of execution time to period'])

        if(ToO['DLP'] in cfg[ToO['UMP']].keys()):
            ancestors = list(nx.ancestors(dag, node_i))
            anc_periods = []
            for ancestor in ancestors:
                if 'period' in list(dag.nodes[ancestor].keys()):
                    anc_periods.append(dag.nodes[ancestor]['period'])
            if(anc_periods):
                lower_bound = max(max(anc_periods), lower_bound)

        ### choices - lower_bound
        choices = cfg[ToO['UMP']][ToO['P']]['Random']
        if(lower_bound):
            choices = [p for p in choices if p >= lower_bound]
            if(not choices):
                raise NoSettablePeriodError()

        return random.choice(choices)
    
    def set_period_all(cfg, G: nx.DiGraph) -> None:
        for node_i in G.nodes():
            G.nodes[node_i]['period'] = random_get_period(node_i, cfg, G)

    def set_period_entry(cfg, G: nx.DiGraph) -> None:
        entry_nodes = [v for v, d in G.in_degree() if d == 0]
        if(ToO['ENP'] in cfg[ToO['UMP']].keys()):
            if('Random' in cfg[ToO['UMP']][ToO['ENP']]):
                unused_periods = copy.deepcopy(cfg[ToO['UMP']][ToO['ENP']]['Random'])
                for entry_i in entry_nodes:
                    if(not unused_periods):
                        unused_periods = copy.deepcopy(cfg[ToO['UMP']][ToO['ENP']]['Random'])
                    choose_period = random.choice(unused_periods)
                    G.nodes[entry_i]['period'] = choose_period
                    unused_periods.remove(choose_period)
            elif('Fixed' in cfg[ToO['UMP']][ToO['ENP']]):
                for entry_i in entry_nodes:
                    G.nodes[entry_i]['period'] = cfg[ToO['UMP']][ToO['ENP']]['Fixed']
        else:
            for entry_i in entry_nodes:
                G.nodes[entry_i]['period'] = random_get_period(entry_i, cfg, G)

    def set_period_exit(cfg, G: nx.DiGraph) -> None:
        exit_nodes = [v for v, d in G.out_degree() if d == 0]
        if(ToO['EXP'] in cfg[ToO['UMP']].keys()):
            if('Random' in cfg[ToO['UMP']][ToO['EXP']]):
                unused_periods = copy.deepcopy(cfg[ToO['UMP']][ToO['EXP']]['Random'])
                for exit_i in exit_nodes:
                    if(not unused_periods):
                        unused_periods = copy.deepcopy(cfg[ToO['UMP']][ToO['EXP']]['Random'])
                    choose_period = random.choice(unused_periods)
                    G.nodes[exit_i]['period'] = choose_period
                    unused_periods.remove(choose_period)
            elif('Fixed' in cfg[ToO['UMP']][ToO['EXP']]):
                for exit_i in exit_nodes:
                    G.nodes[exit_i]['period'] = cfg[ToO['UMP']][ToO['EXP']]['Fixed']
        else:
            for exit_i in exit_nodes:
                G.nodes[exit_i]['period'] = random_get_period(exit_i, cfg, G)

    if(cfg['Use multi-period']['Periodic type'] == 'All'):
        set_period_all(cfg, G)
    elif(cfg['Use multi-period']['Periodic type'] == 'Entry'):
        set_period_entry(cfg, G)
    elif(cfg['Use multi-period']['Periodic type'] == 'IO'):
        set_period_entry(cfg, G)
        set_period_exit(cfg, G)
    # elif(cfg['Use multi-period']['Periodic type'] == 'Chain'):
    #     _set_period_chain(cfg, G, chains)

    if('Entry node periods' in cfg['Use multi-period'].keys()):
        set_period_entry(cfg, G)
    if('Exit node periods' in cfg['Use multi-period'].keys()):
        set_period_exit(cfg, G)
