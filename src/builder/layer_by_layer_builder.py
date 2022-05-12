
from logging import getLogger
from typing import Generator

import networkx as nx
from src.builder.dag_builder_base import DAGBuilderBase
from src.config import Config

logger = getLogger(__name__)


class LayerByLayerBuilder(DAGBuilderBase):
    def __init__(
        self,
        cfg: Config
    ) -> None:
        super().__init__(cfg)

    def build(self) -> Generator[nx.DiGraph, None, None]:
        print(self._cfg.get_value('Number of DAGs'))
        for dag_i in range(self.cfg['Number of DAGs']):
            G = nx.DiGraph()
