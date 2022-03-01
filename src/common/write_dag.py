import networkx as nx
import pydot


def write_dag(config, dest_dir, filename, G : nx.DiGraph) -> None:
    # draw node label
    for node_i in range(G.number_of_nodes()):
        G.nodes[node_i]['label'] = f'[{node_i}]\n' \
                                   f'C: {G.nodes[node_i]["execution_time"]}'
        if('period' in list(G.nodes[node_i].keys())):
            G.nodes[node_i]['shape'] = 'box'
            G.nodes[node_i]['label'] += f'\nT: {G.nodes[node_i]["period"]}'
        if('deadline' in list(G.nodes[node_i].keys())):
            G.nodes[node_i]['style'] = 'bold'
            G.nodes[node_i]['label'] += f'\nD: {G.nodes[node_i]["deadline"]}'
    
    # draw communication time
    if('Use communication time' in config.keys()):
        for start_i, end_i in G.edges():
            G.edges[start_i, end_i]['label'] = f'{G.edges[start_i, end_i]["communication_time"]}'
    
    # write
    pdot = nx.drawing.nx_pydot.to_pydot(G)
    fig_formats = [k for k, v in config['Figure'].items() if v]
    if('png' in fig_formats):
        pdot.write_png(f'{dest_dir}/{filename}.png')
    if('svg' in fig_formats):
        pdot.write_svg(f'{dest_dir}/{filename}.svg')
    if('pdf' in fig_formats):
        pdot.write_pdf(f'{dest_dir}/{filename}.pdf')