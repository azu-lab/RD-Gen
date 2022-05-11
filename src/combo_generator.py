from typing import Dict

from src.config_loader import ConfigLoaderBase
from src.format import Format


class ComboGenerator(ConfigLoaderBase):
    def __init__(
            self,
            format: Format,
            cfg_raw: Dict
    ) -> None:
        super().__init__(format, cfg_raw)
