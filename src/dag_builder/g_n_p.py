from ..config import Config
from .dag_builder_base import DAGBuilderBase


class GNP(DAGBuilderBase):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
