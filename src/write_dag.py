import networkx as nx
import pydot


def write_dag(config, dest_dir, filename, G : nx.DiGraph) -> None:
    for node_i in range(G.number_of_nodes()):
        if(G.nodes[node_i]['timer_driven']):
            G.nodes[node_i]['shape'] = 'box'
            G.nodes[node_i]['label'] = f'[{node_i}]\n' \
                                       f'C: {G.nodes[node_i]["execution_time"]}' \
                                       f'T: {G.nodes[node_i]["Period"]}'
        else:
            G.nodes[node_i]['label'] = f'[{node_i}]\n' \
                                       f'C: {G.nodes[node_i]["execution_time"]}'
    
    # draw communication time
    if('Use communication time' in config.keys()):
        for start_i, end_i in G.edges():
            G.edges[start_i, end_i]['label'] = f'{G.edges[start_i, end_i]["communication_time"]}'
    
    # write
    pdot = nx.drawing.nx_pydot.to_pydot(G)
    pdot.write_png(f'{dest_dir}/{filename}.png', prog='dot')