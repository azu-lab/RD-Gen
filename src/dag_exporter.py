import json
import subprocess

import networkx as nx
import yaml
from networkx.readwrite import json_graph

from src.config import Config


class DAGExporter():
    def __init__(
        self,
        cfg: Config
    ) -> None:
        self._cfg = cfg

    def _export_dag(
        self,
        dest_dir: str,
        filename: str,
        G: nx.DiGraph
    ) -> None:
        if self._cfg.get_value(["OF", "DAG", "YAML"]):
            data = json_graph.node_link_data(G)
            s = json.dumps(data)
            dic = json.loads(s)
            with open(f'{dest_dir}/{filename}.yaml', 'w') as f:
                yaml.dump(dic, f)

        if self._cfg.get_value(["OF", "DAG", "JSON"]):
            data = json_graph.node_link_data(G)
            s = json.dumps(data)
            with open(f'{dest_dir}/{filename}.json', 'w') as f:
                json.dump(s, f)

        if self._cfg.get_value(["OF", "DAG", "DOT"]):
            nx.drawing.nx_pydot.write_dot(
                G, f'{dest_dir}/{filename}.dot')

        if self._cfg.get_value(["OF", "DAG", "XML"]):
            nx.write_graphml_xml(G, f'{dest_dir}/{filename}.xml')

    def _export_fig(
        self,
        dest_dir: str,
        filename: str,
        G: nx.DiGraph
    ) -> None:
        # Preprocessing
        for node_i in G.nodes():
            G.nodes[node_i]['label'] = (
                f'[{node_i}]\n'
                f'C: {G.nodes[node_i]["Execution_time"]}'
            )
            if(period := G.nodes[node_i].get("Period")):
                G.nodes[node_i]['shape'] = 'box'
                G.nodes[node_i]['label'] += f'\nT: {period}'
            if(deadline := G.nodes[node_i].get("End_to_end_deadline")):
                G.nodes[node_i]['style'] = 'bold'
                G.nodes[node_i]['label'] += f'\nD: {deadline}'

        for src_i, tgt_i in G.edges():
            if comm := G.edges[src_i, tgt_i].get("Communication_time"):
                G.edges[src_i, tgt_i]['label'] = f' {comm}'
                G.edges[src_i, tgt_i]['fontsize'] = 10

        # Add legend
        if self._cfg.get_value(["OF", "FIG", "DL"]):
            legend_str = ['----- Legend ----\n\n',
                          'Circle node:  Event-driven node\l',
                          '[i]:  Task index\l',
                          'C:  Worst-case execution time (WCET)\l']
            if(self._cfg.get_value(["PP", "MR"])):
                legend_str.insert(1, 'Square node:  Timer-driven node\l')
                legend_str.append('T:  Period\l')
            if(self._cfg.get_value(["PP", "EED"])):
                legend_str.append('D:  End-to-end deadline\l')
            if(self._cfg.get_value(["PP", "CT"])):
                legend_str.append(
                    'Number attached to arrow:  Communication time\l')
            G.add_node(-1, label=''.join(legend_str),
                       fontsize=15, shape='box3d')

        # Export
        pdot = nx.drawing.nx_pydot.to_pydot(G)
        if(self._cfg.get_value(["OF", "FIG", "PNG"])):
            pdot.write_png(f'{dest_dir}/{filename}.png')
        if(self._cfg.get_value(["OF", "FIG", "SVG"])):
            pdot.write_svg(f'{dest_dir}/{filename}.svg')
        if(self._cfg.get_value(["OF", "FIG", "PDF"])):
            pdot.write_pdf(f'{dest_dir}/{filename}.pdf')
        if(self._cfg.get_value(["OF", "FIG", "EPS"])):
            pdot.write_ps(f'{dest_dir}/{filename}.ps')
            subprocess.run(
                f"eps2eps {dest_dir}/{filename}.ps {dest_dir}/{filename}.eps \
                && rm {dest_dir}/{filename}.ps",
                shell=True
            )

    def export(
        self,
        dest_dir: str,
        filename: str,
        G: nx.DiGraph
    ) -> None:
        self._export_dag(dest_dir, filename, G)
        self._export_fig(dest_dir, filename, G)
