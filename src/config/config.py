import random
from typing import Any, Optional

from ..common import Util


class Config:
    """Config class

    This class provides the value of the config entered by the property.
    The property names of this class correspond to all parameter names at any level.

    Notes
    -----
    If the structure of the configuration file changes, this class must be reprogrammed.

    """

    def __init__(self, config_raw: dict) -> None:
        self.seed = config_raw["Seed"]
        self.number_of_dags = config_raw["Number of DAGs"]
        self.graph_structure = config_raw["Graph structure"]
        self.properties = config_raw["Properties"]
        self.output_formats = config_raw["Output formats"]

    def update_param_value(self, param_name: str, value: Any) -> None:
        """Update parameter value.

        Parameters
        ----------
        param_name : str
            Parameter name.
        value : Any
            Value to be set.

        """
        property_name = Util.convert_to_property(param_name)
        if hasattr(self, property_name):
            object.__setattr__(self, property_name, value)
        else:  # Additional properties
            if self.node_properties and param_name in self.node_properties.keys():
                self.node_properties[param_name] = value
            elif self.edge_properties and param_name in self.edge_properties.keys():
                self.edge_properties[param_name] = value

    def set_random_seed(self) -> None:
        random.seed(self.seed)

    def optimize(self) -> None:
        """Remove 'Random' and 'Fixed'"""
        self._remove_random_fixed(self.graph_structure)
        self._remove_random_fixed(self.properties)

    @staticmethod
    def _remove_random_fixed(param_dict: dict) -> None:
        for k, v in param_dict.items():
            if isinstance(v, dict):
                if set(v.keys()) <= {"Random", "Fixed"}:
                    # Remove
                    value = list(v.values())
                    assert len(value) == 1
                    param_dict[k] = value[0]
                else:
                    Config._remove_random_fixed(v)

    # ----- Graph Structure -----
    @property
    def generation_method(self):
        return self.graph_structure.get("Generation method")

    @property
    def number_of_nodes(self):
        return self.graph_structure.get("Number of nodes")

    @number_of_nodes.setter
    def number_of_nodes(self, value):
        self.graph_structure["Number of nodes"] = value

    @property
    def ensure_weakly_connected(self):
        return self.graph_structure.get("Ensure weakly connected")

    @property
    def out_degree(self):
        return self.graph_structure.get("Out-degree")

    @out_degree.setter
    def out_degree(self, value):
        self.graph_structure["Out-degree"] = value

    @property
    def in_degree(self):
        return self.graph_structure.get("In-degree")

    @in_degree.setter
    def in_degree(self, value):
        self.graph_structure["In-degree"] = value

    @property
    def probability_of_edge(self):
        return self.graph_structure.get("Probability of edge")

    @probability_of_edge.setter
    def probability_of_edge(self, value):
        self.graph_structure["Probability of edge"] = value

    @property
    def number_of_chains(self):
        return self.graph_structure.get("Number of chains")

    @number_of_chains.setter
    def number_of_chains(self, value):
        self.graph_structure["Number of chains"] = value

    @property
    def main_sequence_length(self):
        return self.graph_structure.get("Main sequence length")

    @main_sequence_length.setter
    def main_sequence_length(self, value):
        self.graph_structure["Main sequence length"] = value

    @property
    def number_of_sub_sequences(self):
        return self.graph_structure.get("Number of sub sequences")

    @number_of_sub_sequences.setter
    def number_of_sub_sequences(self, value):
        self.graph_structure["Number of sub sequences"] = value

    @property
    def vertically_link_chains(self):
        return self.graph_structure.get("Vertically link chains")

    @property
    def main_sequence_tail(self):
        if self.vertically_link_chains:
            return self.graph_structure["Vertically link chains"].get("Main sequence tail")
        else:
            return None

    @main_sequence_tail.setter
    def main_sequence_tail(self, value):
        self.graph_structure["Vertically link chains"]["Main sequence tail"] = value

    @property
    def sub_sequence_tail(self):
        if self.vertically_link_chains:
            return self.graph_structure["Vertically link chains"].get("Sub sequence tail")
        else:
            return None

    @sub_sequence_tail.setter
    def sub_sequence_tail(self, value):
        self.graph_structure["Vertically link chains"]["Sub sequence tail"] = value

    @property
    def number_of_entry_nodes(self):
        if Util.ambiguous_equals(self.generation_method, "chain-based"):
            if self.vertically_link_chains:
                return self.graph_structure["Vertically link chains"].get("Number of source nodes")
            else:
                return None
        else:
            return self.graph_structure.get("Number of source nodes")

    @number_of_entry_nodes.setter
    def number_of_entry_nodes(self, value):
        if Util.ambiguous_equals(self.generation_method, "chain-based"):
            self.graph_structure["Vertically link chains"]["Number of source nodes"] = value
        else:
            self.graph_structure["Number of source nodes"] = value

    @property
    def merge_chains(self):
        return self.graph_structure.get("Merge chains")

    @property
    def middle_of_chain(self):
        if self.merge_chains:
            return self.graph_structure["Merge chains"].get("Middle of chain")
        else:
            return None

    @middle_of_chain.setter
    def middle_of_chain(self, value):
        self.graph_structure["Merge chains"]["Middle of chain"] = value

    @property
    def exit_node(self):
        if self.merge_chains:
            return self.graph_structure["Merge chains"].get("Sink node")
        else:
            return None

    @exit_node.setter
    def exit_node(self, value):
        self.graph_structure["Merge chains"]["Sink node"] = value

    @property
    def number_of_exit_nodes(self):
        if Util.ambiguous_equals(self.generation_method, "chain-based"):
            if self.merge_chains:
                return self.graph_structure["Merge chains"].get("Number of sink nodes")
            else:
                return None
        else:
            return self.graph_structure.get("Number of sink nodes")

    @number_of_exit_nodes.setter
    def number_of_exit_nodes(self, value):
        if Util.ambiguous_equals(self.generation_method, "chain-based"):
            self.graph_structure["Merge chains"]["Number of sink nodes"] = value
        else:
            self.graph_structure["Number of sink nodes"] = value

    # ----- Properties -----
    @property
    def execution_time(self):
        return self.properties.get("Execution time")

    @execution_time.setter
    def execution_time(self, value):
        self.properties["Execution time"] = value

    @property
    def communication_time(self):
        return self.properties.get("Communication time")

    @communication_time.setter
    def communication_time(self, value):
        self.properties["Communication time"] = value

    @property
    def ccr(self):
        return self.properties.get("CCR")

    @ccr.setter
    def ccr(self, value):
        self.properties["CCR"] = value

    @property
    def end_to_end_deadline(self):
        return self.properties.get("End-to-end deadline")

    @property
    def ratio_of_deadline_to_critical_path(self):
        if self.end_to_end_deadline:
            return self.properties["End-to-end deadline"].get("Ratio of deadline to critical path")
        else:
            return None

    @ratio_of_deadline_to_critical_path.setter
    def ratio_of_deadline_to_critical_path(self, value):
        self.properties["End-to-end deadline"]["Ratio of deadline to critical path"] = value

    @property
    def multi_rate(self):
        return self.properties.get("Multi-rate")

    @property
    def periodic_type(self):
        if self.multi_rate:
            return self.properties["Multi-rate"].get("Periodic type")
        else:
            return None

    @periodic_type.setter
    def periodic_type(self, value):
        self.properties["Multi-rate"]["Periodic type"] = value

    @property
    def period(self):
        if self.multi_rate:
            return self.properties["Multi-rate"].get("Period")
        else:
            return None

    @period.setter
    def period(self, value):
        self.properties["Multi-rate"]["Period"] = value

    @property
    def entry_node_period(self):
        if self.multi_rate:
            return self.properties["Multi-rate"].get("Source node period")
        else:
            return None

    @entry_node_period.setter
    def entry_node_period(self, value):
        self.properties["Multi-rate"]["Source node period"] = value

    @property
    def exit_node_period(self):
        if self.multi_rate:
            return self.properties["Multi-rate"].get("Sink node period")
        else:
            return None

    @exit_node_period.setter
    def exit_node_period(self, value):
        self.properties["Multi-rate"]["Sink node period"] = value

    @property
    def offset(self):
        if self.multi_rate:
            return self.properties["Multi-rate"].get("Offset")
        else:
            return None

    @offset.setter
    def offset(self, value):
        self.properties["Multi-rate"]["Offset"] = value

    @property
    def total_utilization(self):
        if self.multi_rate:
            return self.properties["Multi-rate"].get("Total utilization")
        else:
            return None

    @total_utilization.setter
    def total_utilization(self, value):
        self.properties["Multi-rate"]["Total utilization"] = value

    @property
    def maximum_utilization(self):
        if self.multi_rate:
            return self.properties["Multi-rate"].get("Maximum utilization")
        else:
            return None

    @maximum_utilization.setter
    def maximum_utilization(self, value):
        self.properties["Multi-rate"]["Maximum utilization"] = value

    @property
    def additional_properties(self) -> Optional[dict]:
        return self.properties.get("Additional properties")

    @property
    def node_properties(self) -> Optional[dict]:
        additional_properties = self.additional_properties
        if additional_properties:
            return additional_properties.get("Node properties")
        else:
            return None

    @property
    def edge_properties(self) -> Optional[dict]:
        additional_properties = self.additional_properties
        if additional_properties:
            return additional_properties.get("Edge properties")
        else:
            return None

    # ----- Output formats -----
    @property
    def naming_of_combination_directory(self):
        return self.output_formats.get("Naming of combination directory")

    @property
    def yaml(self):
        return self.output_formats["DAG"].get("YAML")

    @property
    def json(self):
        return self.output_formats["DAG"].get("JSON")

    @property
    def xml(self):
        return self.output_formats["DAG"].get("XML")

    @property
    def dot(self):
        return self.output_formats["DAG"].get("DOT")

    @property
    def figure(self):
        return self.output_formats.get("Figure")

    @property
    def draw_legend(self):
        if self.figure:
            return self.output_formats["Figure"].get("Draw legend")
        else:
            return None

    @property
    def png(self):
        if self.figure:
            return self.output_formats["Figure"].get("PNG")
        else:
            return None

    @property
    def svg(self):
        if self.figure:
            return self.output_formats["Figure"].get("SVG")
        else:
            return None

    @property
    def eps(self):
        if self.figure:
            return self.output_formats["Figure"].get("EPS")
        else:
            return None

    @property
    def pdf(self):
        if self.figure:
            return self.output_formats["Figure"].get("PDF")
        else:
            return None
