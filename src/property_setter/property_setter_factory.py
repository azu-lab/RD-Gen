from ..config import Config
from .property_setter_base import PropertySetterBase
from .random_setter import RandomSetter


class PropertySetterFactory:
    """Property setter factory class."""

    @staticmethod
    def create_utilization_setter(config: Config) -> PropertySetterBase:
        pass

    @staticmethod
    def create_ccr_setter(config: Config) -> PropertySetterBase:
        pass

    @staticmethod
    def create_deadline_setter(config: Config) -> PropertySetterBase:
        pass

    @staticmethod
    def create_random_setter(
        config: Config, parameter_name: str, target: str
    ) -> PropertySetterBase:
        return RandomSetter(config, parameter_name, target)

    @staticmethod
    def create_additional_setter(config: Config) -> PropertySetterBase:
        pass
