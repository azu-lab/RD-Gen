from typing import List

import networkx as nx
from src.config import Config
from src.property_setter.end_to_end_deadline_setter import E2EDeadlineSetter
from src.property_setter.EPU_setter import EPUSetter
from src.property_setter.property_setter_base import PropertySetterBase
from src.property_setter.random_property_setter import RandomPropertySetter


class PropertySetter():
    def __init__(
        self,
        cfg: Config
    ) -> None:
        self._setters: List[PropertySetterBase] = []

        # Random properties
        if choices := cfg.get_value(["PP", "CT"]):
            self._setters.append(
                RandomPropertySetter("Communication time", choices, "edge")
            )
        if choices := cfg.get_value(["PP", "MP", "OS"]):
            self._setters.append(
                RandomPropertySetter("Offset", choices, "node")
            )
        if node_properties := cfg.get_param(["PP", "AP", "NP"]):
            for child in node_properties.children.values():
                self._setters.append(
                    RandomPropertySetter(
                        child.name.capitalize(),
                        child.value,
                        "node")
                )
        if edge_properties := cfg.get_param(["PP", "AP", "EP"]):
            for child in edge_properties.children.values():
                self._setters.append(
                    RandomPropertySetter(
                        child.name.capitalize(),
                        child.value,
                        "edge")
                )

        # execution time & period & utilization
        self._setters.append(EPUSetter(cfg))

        # End-to-end deadline
        if param := cfg.get_param(["PP", "EED"]):
            self._setters.append(E2EDeadlineSetter(param))

    def set(
        self,
        G: nx.DiGraph
    ) -> None:
        for setter in self._setters:
            setter.set(G)
