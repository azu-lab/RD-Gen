from typing import Generator

import networkx as nx

from ..common import Util
from ..config import Config
from .branching_augmentor import BranchingAugmentor
from .chain_based_builder import ChainBasedBuilder
from .dag_builder_base import DAGBuilderBase
from .fan_in_fan_out_builder import FanInFanOutBuilder
from .g_n_p_builder import GNPBuilder


class _AugmentedBuilder(DAGBuilderBase):
    def __init__(self, base: DAGBuilderBase, config: Config, layout_hint: str) -> None:
        self._base = base
        self._config = config
        self._max_try = 100
        self._augmentor = BranchingAugmentor(config)
        self._layout_hint = layout_hint

    def _validate_config(self, config: Config):
        pass  # base builder already validated

    def build(self) -> Generator[nx.DiGraph, None, None]:
        for g in self._base.build():
            # BranchingAugmentor calls dag.copy() internally; subclasses like
            # ChainBasedDAG cannot be copied via nx default path (constructor
            # requires positional args), so normalise to a plain DiGraph first.
            plain = nx.DiGraph(g)
            yield self._augmentor.augment(plain, self._layout_hint)


class DAGBuilderFactory:
    """DAG builder factory class."""

    @staticmethod
    def create_instance(config: Config) -> DAGBuilderBase:
        gm = config.generation_method
        if Util.ambiguous_equals(gm, "fan-in/fan-out"):
            base = FanInFanOutBuilder(config)
            hint = "fanin"
        elif Util.ambiguous_equals(gm, "g(n, p)"):
            base = GNPBuilder(config)
            hint = "gnp"
        elif Util.ambiguous_equals(gm, "chain-based"):
            base = ChainBasedBuilder(config)
            hint = "chain"
        else:
            raise NotImplementedError
        if config.branching is None or hint is None:
            return base
        return _AugmentedBuilder(base, config, hint)
