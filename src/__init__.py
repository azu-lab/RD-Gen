from logging import DEBUG, Formatter, StreamHandler, getLogger

from .config import ComboGenerator, Config, ConfigValidator
from .dag_builder import DAGBuilderFactory
from .dag_exporter import DAGExporter
from .exceptions import BuildFailedError
from .property_setter import PropertySetterBase, PropertySetterFactory

__all__ = [
    "ConfigValidator",
    "Config",
    "ComboGenerator",
    "DAGBuilderFactory",
    "PropertySetterBase",
    "PropertySetterFactory",
    "DAGExporter",
    "BuildFailedError",
]


# Logger setting
handler = StreamHandler()
handler.setLevel(DEBUG)

fmt = "%(levelname)-8s: %(asctime)s | %(message)s"
formatter = Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)

logger = getLogger()
logger.setLevel(DEBUG)
logger.addHandler(handler)
