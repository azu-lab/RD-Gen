from abc import ABCMeta, abstractmethod
from typing import Generator

import networkx as nx
from src.config import Config


class DAGBuilderBase(metaclass=ABCMeta):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        self._cfg = cfg

    @abstractmethod
    def build(self) -> Generator[nx.DiGraph, None, None]:
        raise NotImplementedError
