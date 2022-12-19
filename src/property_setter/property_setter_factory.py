from ..config import Config
from .additional_setter import AdditionalSetter
from .ccr_setter import CCRSetter
from .deadline_setter import DeadlineSetter
from .property_setter_base import PropertySetterBase
from .random_setter import RandomSetter


class PropertySetterFactory:
    """Property setter factory class."""

    @staticmethod
    def create_utilization_setter(config: Config) -> PropertySetterBase:
        pass

    @staticmethod
    def create_ccr_setter(config: Config) -> CCRSetter:
        """Create CCR setter.

        Parameters
        ----------
        config : Config
            Config.

        Returns
        -------
        CCRSetter
            CCR setter.

        """
        return CCRSetter(config)

    @staticmethod
    def create_deadline_setter(config: Config) -> DeadlineSetter:
        """Create deadline setter.

        Parameters
        ----------
        config : Config
            Config.

        Returns
        -------
        DeadlineSetter
            Deadline setter.

        """
        return DeadlineSetter(config)

    @staticmethod
    def create_random_setter(config: Config, parameter_name: str, target: str) -> RandomSetter:
        """Create random setter.

        Parameters
        ----------
        config : Config
            Config
        parameter_name : str
            Parameter name
        target : str
            "node" or "edge"

        Returns
        -------
        RandomSetter
            Random setter.

        """
        return RandomSetter(config, parameter_name, target)

    @staticmethod
    def create_additional_setter(config: Config) -> AdditionalSetter:
        """Create additional setter.

        Parameters
        ----------
        config : Config
            Config.

        Returns
        -------
        AdditionalSetter
            Additional setter.

        """
        return AdditionalSetter(config)
