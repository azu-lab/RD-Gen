import random
from typing import List, Optional

from ..common import Util


class AdditionalProperties:
    def __init__(self, additional_properties: dict) -> None:
        self._node_properties = additional_properties["Node properties"]
        self._edge_properties = additional_properties["Edge properties"]

    def get_property_names(self) -> List[str]:
        return list(self._node_properties.keys()) + list(self._edge_properties.keys())

    def get_value(self, property_name: str):
        value = self._node_properties.get(property_name)
        if value is None:
            value = self._edge_properties.get(property_name)

        return value

    def set_value(self, property_name: str, value) -> None:
        if property_name in self._node_properties.keys():
            self._node_properties[property_name] = value
        else:
            self._edge_properties[property_name] = value


class Config:
    """Config class

    This class provides the value of the config entered by the property.
    The property names of this class correspond to all parameter names at any level.
    To obtain the value of 'Additional properties',
    it is necessary to call a function, not a property.

    Notes
    -----
    If the structure of the configuration file changes, this class must be reprogrammed.

    """

    def __init__(self, config_raw: dict) -> None:
        self._seed = config_raw["Seed"]
        self._number_of_dags = config_raw["Number of DAGs"]
        self._graph_structure = config_raw["Graph structure"]
        self._properties = config_raw["Properties"]
        self._additional_properties: Optional[AdditionalProperties]
        if config_raw["Properties"].get("Additional properties"):
            self._additional_properties = AdditionalProperties(
                config_raw["Properties"]["Additional properties"]
            )
            del config_raw["Properties"]["Additional properties"]
        else:
            self._additional_properties = None
        self._output_formats = config_raw["Output formats"]

    # def is_additional(self, param_name: str) -> bool:
    #     if self._additional_properties is None:
    #         return False
    #     additional_property_names = self._additional_properties.get_property_names()
    #     if param_name in additional_property_names:
    #         return True
    #     else:
    #         return False

    # def get_additional_property(self, property_name: str):
    #     return self._additional_properties.get_value(property_name)

    # def set_additional_property(self, property_name: str, value) -> None:
    #     self._additional_properties.set_value(property_name, value)

    def set_random_seed(self) -> None:
        random.seed(self.seed)

    def optimize(self) -> None:
        """Remove 'Random' and 'Fixed'"""
        self._remove_random_fixed(self._graph_structure)
        self._remove_random_fixed(self._properties)
        if self._additional_properties:
            self._additional_properties = AdditionalProperties(
                self._properties["Additional properties"]
            )

    @staticmethod
    def _remove_random_fixed(param_dict: dict) -> None:
        for k, v in param_dict.items():
            if set(v.keys()) <= {"Random", "Fixed"}:
                # Remove
                value = list(v.values())
                assert len(value) == 1
                param_dict[k] = value[0]
                break
            else:
                Config._remove_random_fixed(v)

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def number_of_dags(self) -> int:
        return self._number_of_dags

    # ----- Graph Structure -----
    @property
    def generation_method(self):
        return self._graph_structure.get("Generation method")

    @property
    def number_of_nodes(self):
        return self._graph_structure.get("Number of nodes")

    @number_of_nodes.setter
    def number_of_nodes(self, value):
        self._graph_structure["Number of nodes"] = value

    @property
    def ensure_weakly_connected(self):
        return self._graph_structure.get("Ensure weakly connected")

    @property
    def out_degree(self):
        return self._graph_structure.get("Out-degree")

    @out_degree.setter
    def out_degree(self, value):
        self._graph_structure["Out-degree"] = value

    @property
    def in_degree(self):
        return self._graph_structure.get("In-degree")

    @in_degree.setter
    def in_degree(self, value):
        self._graph_structure["In-degree"] = value

    @property
    def probability_of_edge(self):
        return self._graph_structure.get("Probability of edge")

    @probability_of_edge.setter
    def probability_of_edge(self, value):
        self._graph_structure["Probability of edge"] = value

    @property
    def number_of_chains(self):
        return self._graph_structure.get("Number of chains")

    @number_of_chains.setter
    def number_of_chains(self, value):
        self._graph_structure["Number of chains"] = value

    @property
    def main_sequence_length(self):
        return self._graph_structure.get("Main sequence length")

    @main_sequence_length.setter
    def main_sequence_length(self, value):
        self._graph_structure["Main sequence length"] = value

    @property
    def number_of_sub_sequences(self):
        return self._graph_structure.get("Number of sub sequences")

    @number_of_sub_sequences.setter
    def number_of_sub_sequences(self, value):
        self._graph_structure["Number of sub sequences"] = value

    @property
    def vertically_link_chains(self):
        return self._graph_structure.get("Vertically link chains")

    @property
    def main_sequence_tail(self):
        return self._graph_structure["Vertically link chains"].get("Main sequence tail")

    @main_sequence_tail.setter
    def main_sequence_tail(self, value):
        self._graph_structure["Vertically link chains"]["Main sequence tail"] = value

    @property
    def sub_sequence_tail(self):
        return self._graph_structure["Vertically link chains"].get("Sub sequence tail")

    @sub_sequence_tail.setter
    def sub_sequence_tail(self, value):
        self._graph_structure["Vertically link chains"]["Sub sequence tail"] = value

    @property
    def number_of_entry_nodes(self):
        if Util.ambiguous_equals(self.generation_method, "chain-based"):
            return self._graph_structure["Vertically link chains"].get("Number of entry nodes")
        else:
            return self._graph_structure.get("Number of entry nodes")

    @number_of_entry_nodes.setter
    def number_of_entry_nodes(self, value):
        if Util.ambiguous_equals(self.generation_method, "chain-based"):
            self._graph_structure["Vertically link chains"]["Number of entry nodes"] = value
        else:
            self._graph_structure["Number of entry nodes"] = value

    @property
    def merge_chains(self):
        return self._graph_structure.get("Merge chains")

    @property
    def middle_of_chain(self):
        return self._graph_structure["Merge chains"].get("Middle of chain")

    @middle_of_chain.setter
    def middle_of_chain(self, value):
        self._graph_structure["Merge chains"]["Middle of chain"] = value

    @property
    def exit_node(self):
        return self._graph_structure["Merge chains"].get("Exit node")

    @exit_node.setter
    def exit_node(self, value):
        self._graph_structure["Merge chains"]["Exit node"] = value

    @property
    def number_of_exit_nodes(self):
        if Util.ambiguous_equals(self.generation_method, "chain-based"):
            return self._graph_structure["Merge chains"].get("Number of exit nodes")
        else:
            return self._graph_structure.get("Number of exit nodes")

    @number_of_exit_nodes.setter
    def number_of_exit_nodes(self, value):
        if Util.ambiguous_equals(self.generation_method, "chain-based"):
            self._graph_structure["Merge chains"]["Number of exit nodes"] = value
        else:
            self._graph_structure["Number of exit nodes"] = value

    # ----- Properties -----
    @property
    def execution_time(self):
        return self._properties.get("Execution time")

    @execution_time.setter
    def execution_time(self, value):
        self._properties["Execution time"] = value

    @property
    def communication_time(self):
        return self._properties.get("Communication time")

    @communication_time.setter
    def communication_time(self, value):
        self._properties["Communication time"] = value

    @property
    def ccr(self):
        return self._properties.get("CCR")

    @ccr.setter
    def ccr(self, value):
        self._properties["CCR"] = value

    @property
    def end_to_end_deadline(self):
        return self._properties.get("End-to-end deadline")

    @property
    def ratio_of_deadline_to_critical_path(self):
        return self._properties["End-to-end deadline"].get("Ratio of deadline to critical path")

    @ratio_of_deadline_to_critical_path.setter
    def ratio_of_deadline_to_critical_path(self, value):
        self._properties["End-to-end deadline"]["Ratio of deadline to critical path"] = value

    @property
    def multi_rate(self):
        return self._properties.get("Multi-rate")

    @property
    def periodic_type(self):
        return self._properties["Multi-rate"].get("Periodic type")

    @periodic_type.setter
    def periodic_type(self, value):
        self._properties["Multi-rate"]["Periodic type"] = value

    @property
    def period(self):
        return self._properties["Multi-rate"].get("Period")

    @period.setter
    def period(self, value):
        self._properties["Multi-rate"]["Period"] = value

    @property
    def entry_node_period(self):
        return self._properties["Multi-rate"].get("Entry node period")

    @entry_node_period.setter
    def entry_node_period(self, value):
        self._properties["Multi-rate"]["Entry node period"] = value

    @property
    def exit_node_period(self):
        return self._properties["Multi-rate"].get("Exit node period")

    @exit_node_period.setter
    def exit_node_period(self, value):
        self._properties["Multi-rate"]["Exit node period"] = value

    @property
    def offset(self):
        return self._properties["Multi-rate"].get("Offset")

    @offset.setter
    def offset(self, value):
        self._properties["Multi-rate"]["Offset"] = value

    @property
    def total_utilization(self):
        return self._properties["Multi-rate"].get("Total utilization")

    @total_utilization.setter
    def total_utilization(self, value):
        self._properties["Multi-rate"]["Total utilization"] = value

    @property
    def maximum_utilization(self):
        return self._properties["Multi-rate"].get("Maximum utilization")

    @maximum_utilization.setter
    def maximum_utilization(self, value):
        self._properties["Multi-rate"]["Maximum utilization"] = value

    # ----- Output formats -----
    @property
    def naming_of_combination_directory(self):
        return self._output_formats.get("Naming of combination directory")

    @property
    def yaml(self):
        return self._output_formats["DAG"].get("YAML")

    @property
    def json(self):
        return self._output_formats["DAG"].get("JSON")

    @property
    def xml(self):
        return self._output_formats["DAG"].get("XML")

    @property
    def dot(self):
        return self._output_formats["DAG"].get("DOT")

    @property
    def draw_legend(self):
        return self._output_formats["Figure"].get("Draw legend")

    @property
    def png(self):
        return self._output_formats["Figure"].get("PNG")

    @property
    def svg(self):
        return self._output_formats["Figure"].get("SVG")

    @property
    def eps(self):
        return self._output_formats["Figure"].get("EPS")

    @property
    def pdf(self):
        return self._output_formats["Figure"].get("PDF")
