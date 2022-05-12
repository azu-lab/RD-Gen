from re import L

from src.builder.layer_by_layer import FanInFanOutBuilder, LayerByLayerBuilder
from src.config import Config


class DAGBuilder:
    @staticmethod
    def create_fan_in_fan_out_builder(
        cfg: Config
    ) -> FanInFanOutBuilder:
        return FanInFanOutBuilder(cfg)

    @staticmethod
    def create_layer_by_layer_builder(
        cfg: Config
    ) -> LayerByLayerBuilder:
        return LayerByLayerBuilder(cfg)

    @staticmethod
    def create_chain_based_builder():
        pass  # TODO
