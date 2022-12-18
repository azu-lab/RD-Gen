from ..common import Util
from ..config import Config
from .chain_based import ChainBased
from .dag_builder_base import DAGBuilderBase
from .fan_in_fan_out import FanInFanOut
from .g_n_p import GNP


class DAGBuilderFactory:
    """DAG builder factory class."""

    @staticmethod
    def create_instance(config: Config) -> DAGBuilderBase:
        """Create DAG builder instance.

        Currently supported generation methods:
        - Fan-in/fan-out method (see https://hal.archives-ouvertes.fr/hal-00471255/file/ggen.pdf)
        - G(n, p) method (see https://hal.archives-ouvertes.fr/hal-00471255/file/ggen.pdf)
        - Chain-based method

        Parameters
        ----------
        config : Config
            Config.

        Returns
        -------
        DAGBuilderBase
            DAG builder.

        Raises
        ------
        NotImplementedError
            Not implement.

        """
        generation_method = config.generation_method
        if Util.ambiguous_equals(generation_method, "fan-in/fan-out"):
            return FanInFanOut(config)
        elif Util.ambiguous_equals(generation_method, "g(n, p)"):
            return GNP(config)
        elif Util.ambiguous_equals(generation_method, "chain-based"):
            return ChainBased(config)
        else:
            raise NotImplementedError
