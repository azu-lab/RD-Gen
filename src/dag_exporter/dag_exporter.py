import json
import subprocess

import networkx as nx
import yaml
from networkx.readwrite import json_graph

from ..config import Config


class DAGExporter:
    """DAG exporter class."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def export(self, dag: nx.DiGraph, dest_dir: str, file_name: str) -> None:
        """Export DAG.

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.
        dest_dir : str
            Destination directory.
        file_name : str
            File name.

        """
        self._export_dag(dag, dest_dir, file_name)
        if self._config.figure:
            self._export_fig(dag, dest_dir, file_name)

    def _export_dag(self, dag: nx.DiGraph, dest_dir: str, file_name: str) -> None:
        """Export DAG description file.

        Supported extension: [YAML/JSON/DOT/XML].

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.
        dest_dir : str
            Destination directory.
        file_name : str
            File name.

        """
        if self._config.yaml:
            data = json_graph.node_link_data(dag)
            s = json.dumps(data)
            dic = json.loads(s)
            with open(f"{dest_dir}/{file_name}.yaml", "w") as f:
                yaml.dump(dic, f)

        if self._config.json:
            data = json_graph.node_link_data(dag)
            s = json.dumps(data)
            with open(f"{dest_dir}/{file_name}.json", "w") as f:
                json.dump(s, f)

        if self._config.dot:
            nx.drawing.nx_pydot.write_dot(dag, f"{dest_dir}/{file_name}.dot")

        if self._config.xml:
            nx.write_graphml_xml(dag, f"{dest_dir}/{file_name}.xml")

    def _export_fig(self, dag: nx.DiGraph, dest_dir: str, file_name: str) -> None:
        """Export DAG figure.

        Supported extension: [PNG/PDF/EPS/SVG].

        Parameters
        ----------
        dag : nx.DiGraph
            DAG.
        dest_dir : str
            Destination directory.
        file_name : str
            File name.

        """
        # Preprocessing
        for node_i in dag.nodes():
            dag.nodes[node_i]["label"] = (
                f"[{node_i}]\n" f'C: {dag.nodes[node_i]["Execution time"]}'
            )
            if period := dag.nodes[node_i].get("Period"):
                dag.nodes[node_i]["shape"] = "box"
                dag.nodes[node_i]["label"] += f"\nT: {period}"
            if deadline := dag.nodes[node_i].get("End-to-end deadline"):
                dag.nodes[node_i]["style"] = "bold"
                dag.nodes[node_i]["label"] += f"\nD: {deadline}"

        for src_i, tgt_i in dag.edges():
            if comm := dag.edges[src_i, tgt_i].get("Communication time"):
                dag.edges[src_i, tgt_i]["label"] = f" {comm}"
                dag.edges[src_i, tgt_i]["fontsize"] = 10

        # Add legend
        if self._config.draw_legend:
            legend_str = [
                "----- Legend ----\n\n",
                "Circle node:  Event-driven node\l",
                "[i]:  Task index\l",
                "C:  Worst-case execution time (WCET)\l",
            ]
            if self._config.multi_rate:
                legend_str.insert(1, "Square node:  Timer-driven node\l")
                legend_str.append("T:  Period\l")
            if self._config.end_to_end_deadline:
                legend_str.append("D:  End-to-end deadline\l")
            if self._config.communication_time:
                legend_str.append("Number attached to arrow:  Communication time\l")
            dag.add_node(-1, label="".join(legend_str), fontsize=15, shape="box3d")

        # Export
        pdot = nx.drawing.nx_pydot.to_pydot(dag)
        if self._config.png:
            pdot.write_png(f"{dest_dir}/{file_name}.png")
        if self._config.svg:
            pdot.write_svg(f"{dest_dir}/{file_name}.svg")
        if self._config.pdf:
            pdot.write_pdf(f"{dest_dir}/{file_name}.pdf")
        if self._config.eps:
            pdot.write_ps(f"{dest_dir}/{file_name}.ps")
            subprocess.run(
                f"eps2eps {dest_dir}/{file_name}.ps {dest_dir}/{file_name}.eps \
                && rm {dest_dir}/{file_name}.ps",
                shell=True,
            )
