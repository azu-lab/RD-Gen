from ..config import Config
from .dag_builder_base import DAGBuilderBase


class ChainBased(DAGBuilderBase):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
