import yaml
from pathlib import Path


class ConfigLoader:
    def __init__(self, config_path: str = "config.yaml"):
        self._path = Path(config_path)
        self._data: dict = {}
        self.reload()

    def reload(self):
        with open(self._path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

    def get(self, key: str, default=None):
        keys = key.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, default)
            else:
                return default
        return val

    @property
    def mode(self) -> str:
        return self._data.get("mode", "prod")

    @property
    def sensors(self) -> dict:
        return self._data.get("sensors", {})

    @property
    def ui(self) -> dict:
        return self._data.get("ui", {})

    @property
    def interface(self) -> dict:
        return self._data.get("interface", {})

    @property
    def unload_logic(self) -> dict:
        return self._data.get("unload_logic", {})

    @property
    def logging_config(self) -> dict:
        return self._data.get("logging", {})

    @property
    def error_history(self) -> dict:
        return self._data.get("error_history", {})
