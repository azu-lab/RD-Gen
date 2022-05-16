import networkx as nx
import numpy as np
import random
import copy

from typing import List, Tuple

from src.builder.chain import Chain
from src.abbreviation import TO_ORI, TO_ABB
from src.exceptions import NoSettablePeriodError


def random_set_period(cfg, G: nx.DiGraph, chains: List[Chain] = []) -> None:
    def random_get_period(
        node_i: int,
        cfg,
        dag: nx.DiGraph,
    ) -> int:
        if('Fixed' in cfg[TO_ORI['UMP']][TO_ORI['P']].keys()):
            return cfg[TO_ORI['UMP']][TO_ORI['P']]['Fixed']

        # Determine lower_bound
        lower_bound = None
        if(TO_ORI['DLP'] in cfg[TO_ORI['UMP']].keys()):
            ancestors = list(nx.ancestors(dag, node_i))
            anc_periods = []
            for ancestor in ancestors:
                if 'period' in list(dag.nodes[ancestor].keys()):
                    anc_periods.append(dag.nodes[ancestor]['period'])
            if(anc_periods):
                lower_bound = max(anc_periods)

        ### choices - lower_bound
        choices = cfg[TO_ORI['UMP']][TO_ORI['P']]['Random']
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
        if(TO_ORI['ENP'] in cfg[TO_ORI['UMP']].keys()):
            if('Random' in cfg[TO_ORI['UMP']][TO_ORI['ENP']]):
                unused_periods = copy.deepcopy(
                    cfg[TO_ORI['UMP']][TO_ORI['ENP']]['Random'])
                for entry_i in entry_nodes:
                    if(not unused_periods):
                        unused_periods = copy.deepcopy(
                            cfg[TO_ORI['UMP']][TO_ORI['ENP']]['Random'])
                    choose_period = random.choice(unused_periods)
                    G.nodes[entry_i]['period'] = choose_period
                    unused_periods.remove(choose_period)
            elif('Fixed' in cfg[TO_ORI['UMP']][TO_ORI['ENP']]):
                for entry_i in entry_nodes:
                    G.nodes[entry_i]['period'] = cfg[TO_ORI['UMP']
                                                     ][TO_ORI['ENP']]['Fixed']
        else:
            for entry_i in entry_nodes:
                G.nodes[entry_i]['period'] = random_get_period(entry_i, cfg, G)

    def set_period_exit(cfg, G: nx.DiGraph) -> None:
        exit_nodes = [v for v, d in G.out_degree() if d == 0]
        if(TO_ORI['EXP'] in cfg[TO_ORI['UMP']].keys()):
            if('Random' in cfg[TO_ORI['UMP']][TO_ORI['EXP']]):
                unused_periods = copy.deepcopy(
                    cfg[TO_ORI['UMP']][TO_ORI['EXP']]['Random'])
                for exit_i in exit_nodes:
                    if(not unused_periods):
                        unused_periods = copy.deepcopy(
                            cfg[TO_ORI['UMP']][TO_ORI['EXP']]['Random'])
                    choose_period = random.choice(unused_periods)
                    G.nodes[exit_i]['period'] = choose_period
                    unused_periods.remove(choose_period)
            elif('Fixed' in cfg[TO_ORI['UMP']][TO_ORI['EXP']]):
                for exit_i in exit_nodes:
                    G.nodes[exit_i]['period'] = cfg[TO_ORI['UMP']
                                                    ][TO_ORI['EXP']]['Fixed']
        else:
            for exit_i in exit_nodes:
                G.nodes[exit_i]['period'] = random_get_period(exit_i, cfg, G)

    def set_period_chain(cfg, G: nx.DiGraph, chains: List[Chain]) -> None:
        for chain in chains:
            G.nodes[chain.head]['period'] = random_get_period(
                chain.head, cfg, G)

    if(cfg['Use multi-period']['Periodic type'] == 'All'):
        set_period_all(cfg, G)
    elif(cfg['Use multi-period']['Periodic type'] == 'Entry'):
        set_period_entry(cfg, G)
    elif(cfg['Use multi-period']['Periodic type'] == 'IO'):
        set_period_entry(cfg, G)
        set_period_exit(cfg, G)
    elif(cfg['Use multi-period']['Periodic type'] == 'Chain'):
        set_period_chain(cfg, G, chains)

    if('Entry node periods' in cfg['Use multi-period'].keys()):
        set_period_entry(cfg, G)
    if('Exit node periods' in cfg['Use multi-period'].keys()):
        set_period_exit(cfg, G)
