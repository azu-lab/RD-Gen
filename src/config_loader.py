import yaml

from src.config import Config


class ConfigLoader():
    def __init__(
        self,
        config_path: str
    ) -> None:
        with open(config_path, "r") as f:
            self._cfg_raw = yaml.safe_load(f)
        self._validate()

    def load(self) -> Config:
        return Config(self._cfg_raw)

    def _validate(self) -> None:
        if self._cfg_raw["Generation method"]:
            pass  # TODO
            # config_scheme = Schema()
