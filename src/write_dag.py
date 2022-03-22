import networkx as nx
import yaml
import json
from networkx.readwrite import json_graph


def write_dag(config, dest_dir, filename, G: nx.DiGraph) -> None:
    ### Output DAG description files
    dag_formats = [k for k, v in config['DAG format'].items() if v]
    if('xml' in dag_formats):
        nx.write_graphml_xml(G, f'{dest_dir}/{filename}.xml')
    if('dot' in dag_formats):
        nx.drawing.nx_pydot.write_dot(G, f'{dest_dir}/{filename}.dot')
    if('json' in dag_formats):
        data = json_graph.node_link_data(G)
        s = json.dumps(data)
        with open(f'{dest_dir}/{filename}', 'w') as f:
            json.dump(s, f)
    if('yaml' in dag_formats):
        data = json_graph.node_link_data(G)
        s = json.dumps(data)
        dic = json.loads(s)
        with open(f'{dest_dir}/{filename}.yaml', 'w') as f:
            yaml.dump(dic, f)


    ### Output figures
    # draw node label
    for node_i in range(G.number_of_nodes()):
        G.nodes[node_i]['label'] = f'[{node_i}]\n' \
                                   f'C: {G.nodes[node_i]["exec"]}'
        if('period' in list(G.nodes[node_i].keys())):
            G.nodes[node_i]['shape'] = 'box'
            G.nodes[node_i]['label'] += f'\nT: {G.nodes[node_i]["period"]}'
        if('deadline' in list(G.nodes[node_i].keys())):
            G.nodes[node_i]['style'] = 'bold'
            G.nodes[node_i]['label'] += f'\nD: {G.nodes[node_i]["deadline"]}'

    # draw communication time
    if('Use communication time' in config.keys()):
        for start_i, end_i in G.edges():
            G.edges[start_i, end_i]['label'] = \
                    f'{G.edges[start_i, end_i]["comm"]}'

    pdot = nx.drawing.nx_pydot.to_pydot(G)
    fig_formats = [k for k, v in config['Figure format'].items() if v]
    if('png' in fig_formats):
        pdot.write_png(f'{dest_dir}/{filename}.png')
    if('svg' in fig_formats):
        pdot.write_svg(f'{dest_dir}/{filename}.svg')
    if('pdf' in fig_formats):
        pdot.write_pdf(f'{dest_dir}/{filename}.pdf')
