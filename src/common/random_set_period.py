import networkx as nx


def _set_all(config, G):
    # TODO
    pass


def _set_entry(config, G):
    # TODO
    pass


def _set_random(config, G):
    # TODO
    pass


def _set_chain(config, G):
    # TODO
    pass


def random_set_period(config, mode : str, G : nx.DiGraph) -> None:
    if(mode not in ['normal', 'chain']):
        print('[Error] Invalid mode name was specified.')
        exit(1)
    
    if(config['Use multi-period']['Periodic type'] == 'All'):
        _set_all(config, G)
    elif(config['Use multi-period']['Periodic type'] == 'Entry'):
        _set_entry(config, G)
    elif(config['Use multi-period']['Periodic type'] == 'Random'):
        _set_random(config, G)
    
    if(mode == 'chain' and config['Use multi-period']['Periodic type'] == 'Chain'):
        _set_chain(config, G)