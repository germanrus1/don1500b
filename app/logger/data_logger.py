import csv
from datetime import datetime
from pathlib import Path
from typing import List


class DataLogger:
    _FIELDS = ["timestamp", "event_type", "sensor_name", "value", "unit", "status", "details"]

    def __init__(self, config: dict):
        self._data_dir = Path(config.get("data_dir", "data"))
        self._data_dir.mkdir(exist_ok=True)
        self._date_fmt = config.get("date_format", "%Y-%m-%d")
        self._enabled: bool = config.get("csv_log_enabled", True)

    def log_reading(self, sensor_name: str, value: float, unit: str, status: str):
        self._write("reading", sensor_name, value, unit, status)

    def log_error(self, sensor_name: str, value: float, unit: str, status: str, details: str = ""):
        self._write("error", sensor_name, value, unit, status, details)

    def log_unload(self, count: int, culture: str):
        self._write("unload", "bin_level", count, "count", "success", f"culture={culture}")

    def log_system(self, event: str):
        self._write("system", "system", "", "", "info", event)

    def read_errors(self, max_entries: int = 20) -> List[dict]:
        filepath = self._data_dir / f"{datetime.now().strftime(self._date_fmt)}.csv"
        if not filepath.exists():
            return []
        with open(filepath, encoding="utf-8", newline="") as f:
            rows = [r for r in csv.DictReader(f) if r.get("event_type") == "error"]
        return rows[-max_entries:]

    def _write(self, event_type: str, sensor_name: str, value, unit: str, status: str, details: str = ""):
        if not self._enabled:
            return
        filepath = self._data_dir / f"{datetime.now().strftime(self._date_fmt)}.csv"
        write_header = not filepath.exists()
        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": event_type,
                "sensor_name": sensor_name,
                "value": value,
                "unit": unit,
                "status": status,
                "details": details,
            })
