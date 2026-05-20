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

    def set_and_save(self, key: str, value) -> None:
        """Update a dot-notation key in memory and persist to disk."""
        keys = key.split(".")
        d = self._data
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
