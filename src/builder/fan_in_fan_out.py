
from logging import getLogger
from typing import Generator

import networkx as nx
from src.builder.dag_builder_base import DAGBuilderBase
from src.config import Config

logger = getLogger(__name__)


class FanInFanOutBuilder(DAGBuilderBase):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        super().__init__(cfg)

    def build(self) -> Generator[nx.DiGraph, None, None]:
        for dag_i in range(self._cfg.get_value('NG')):
            G = nx.DiGraph()
            pass  # TODO
