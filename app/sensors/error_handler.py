import time
from typing import Dict, Optional

from app.sensors.sensor_base import SensorStatus


class ErrorHandler:
    """
    Checks sensor values against config thresholds with a grace period.
    Errors on non-drum sensors are suppressed when the drum is not spinning.
    """

    def __init__(self, sensors_config: dict):
        self._cfg = sensors_config
        self._error_since: Dict[str, float] = {}

    def check(self, name: str, value: float, drum_spinning: bool) -> SensorStatus:
        raw = self._raw_status(name, value, drum_spinning)
        now = time.monotonic()

        if raw == SensorStatus.OK:
            self._error_since.pop(name, None)
            return SensorStatus.OK

        if name not in self._error_since:
            self._error_since[name] = now

        grace_ms: float = self._cfg.get(name, {}).get("error_duration_ms", 0)
        elapsed_ms = (now - self._error_since[name]) * 1000

        if elapsed_ms >= grace_ms:
            return raw

        return SensorStatus.OK

    def _raw_status(self, name: str, value: float, drum_spinning: bool) -> SensorStatus:
        if name != "drum" and not drum_spinning:
            self._error_since.pop(name, None)
            return SensorStatus.OK

        cfg = self._cfg.get(name, {})
        if cfg.get("type") != "impulse":
            return SensorStatus.OK

        critical: Optional[float] = cfg.get("error_threshold_low")
        warn_low: Optional[float] = cfg.get("warn_low")
        warn_high: Optional[float] = cfg.get("warn_high")

        if critical is not None and value <= critical:
            return SensorStatus.CRITICAL
        if warn_low is not None and value < warn_low:
            return SensorStatus.WARN_LOW
        if warn_high is not None and value > warn_high:
            return SensorStatus.WARN_HIGH

        return SensorStatus.OK
