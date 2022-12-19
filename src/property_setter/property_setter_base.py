from abc import ABCMeta, abstractmethod

import networkx as nx

from ..config import Config


class PropertySetterBase(metaclass=ABCMeta):
    def __init__(self, config: Config) -> None:
        self._validate_config(config)
        self._config = config

    @abstractmethod
    def set(self, dag: nx.DiGraph) -> None:
        raise NotImplementedError

    @abstractmethod
    def _validate_config(self, config: Config) -> None:
        raise NotImplementedError
