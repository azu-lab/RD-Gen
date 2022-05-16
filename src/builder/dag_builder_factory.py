
from src.builder.chain_based import ChainBasedBuilder
from src.builder.fan_in_fan_out import FanInFanOutBuilder
from src.builder.g_n_p import GNPBuilder
from src.config import Config


class DAGBuilder:
    @staticmethod
    def create_fan_in_fan_out_builder(
        cfg: Config
    ) -> FanInFanOutBuilder:
        return FanInFanOutBuilder(cfg)

    @staticmethod
    def create_g_n_p_builder(
        cfg: Config
    ) -> GNPBuilder:
        return GNPBuilder(cfg)

    @staticmethod
    def create_chain_based_builder(
        cfg: Config
    ) -> ChainBasedBuilder:
        return ChainBasedBuilder(cfg)
