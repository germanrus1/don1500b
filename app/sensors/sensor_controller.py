import threading
import time
from collections import deque
from datetime import datetime
from typing import Dict, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from app.config.config_loader import ConfigLoader
from app.sensors.sensor_base import SensorReading, SensorStatus
from app.sensors.error_handler import ErrorHandler
from app.sensors.unload_logic import UnloadLogic


class _ImpulseCounter:
    """Thread-safe pulse counter with a rolling 2-second window for RPM calculation."""

    WINDOW = 2.0
    MAX_STORED = 600

    def __init__(self):
        self._times: deque = deque(maxlen=self.MAX_STORED)
        self._lock = threading.Lock()

    def on_pulse(self, *_args):
        now = time.monotonic()
        with self._lock:
            self._times.append(now)

    def rpm(self) -> float:
        now = time.monotonic()
        cutoff = now - self.WINDOW
        with self._lock:
            recent = sum(1 for t in self._times if t >= cutoff)
        return (recent / self.WINDOW) * 60.0


class SensorController(QThread):
    state_updated = pyqtSignal(dict)   # Dict[str, SensorReading]
    unload_detected = pyqtSignal(int)  # unload count

    def __init__(self, config: ConfigLoader):
        super().__init__()
        self._config = config
        self._running = False
        self._counters: Dict[str, _ImpulseCounter] = {}
        self._gpio = None
        self._mock = None

        sensors_list = config.sensors.get("list", {})
        self._error_handler = ErrorHandler(sensors_list)
        self._unload_logic = UnloadLogic(config.unload_logic)
        self._unload_logic.on_unload = lambda count: self.unload_detected.emit(count)

        self._setup(sensors_list)

    # ── Setup ──────────────────────────────────────────────────────────────

    def _setup(self, sensors_list: dict):
        if self._config.mode != "prod":
            self._setup_mock(sensors_list)
            return
        try:
            self._setup_gpio(sensors_list)
        except (ImportError, RuntimeError, Exception) as exc:
            print(f"[SensorController] GPIO unavailable ({exc}), using mock mode")
            self._setup_mock(sensors_list)

    def _setup_gpio(self, sensors_list: dict):
        import RPi.GPIO as GPIO  # noqa: PLC0415
        self._gpio = GPIO
        GPIO.setmode(GPIO.BCM)
        for name, cfg in sensors_list.items():
            pin = cfg.get("gpio")
            if pin is None:
                continue
            GPIO.setup(pin, GPIO.IN)
            if cfg.get("type") == "impulse":
                counter = _ImpulseCounter()
                self._counters[name] = counter
                GPIO.add_event_detect(
                    pin, GPIO.RISING,
                    callback=counter.on_pulse,
                    bouncetime=cfg.get("debounce_ms", 50),
                )

    def _setup_mock(self, sensors_list: dict):
        from app.dev.mock_sensors import MockSensors
        self._mock = MockSensors(sensors_list)
        for name, cfg in sensors_list.items():
            if cfg.get("type") == "impulse":
                counter = _ImpulseCounter()
                self._counters[name] = counter
                self._mock.register_pulse_callback(name, counter.on_pulse)
        self._mock.start()

    # ── Thread loop ────────────────────────────────────────────────────────

    def run(self):
        self._running = True
        sensors_list = self._config.sensors.get("list", {})
        hz = self._config.interface.get("ui_update_frequency_hz", 10)
        interval = 1.0 / hz

        while self._running:
            readings = self._read_all(sensors_list)
            self.state_updated.emit(readings)
            time.sleep(interval)

    def stop(self):
        self._running = False
        if self._mock:
            self._mock.stop()
        if self._gpio:
            try:
                self._gpio.cleanup()
            except Exception:
                pass

    # ── State building ─────────────────────────────────────────────────────

    def _read_all(self, sensors_list: dict) -> dict:
        drum_cfg = sensors_list.get("drum", {})
        drum_rpm = self._counters["drum"].rpm() if "drum" in self._counters else 0.0
        drum_spinning = drum_rpm > drum_cfg.get("error_threshold_low", 100)

        readings: Dict[str, SensorReading] = {}

        for name, cfg in sensors_list.items():
            sensor_type = cfg.get("type")

            if sensor_type == "impulse":
                value = self._counters[name].rpm() if name in self._counters else 0.0
                unit = cfg.get("units", "об/мин")
                status = self._error_handler.check(name, value, drum_spinning)

            elif sensor_type == "discrete":
                if self._mock:
                    value = float(self._mock.get_discrete_value(name))
                elif self._gpio and cfg.get("gpio") is not None:
                    value = float(self._gpio.input(cfg["gpio"]))
                else:
                    value = 0.0
                unit = cfg.get("units", "статус")
                status = SensorStatus.OK
                if name == "bin_level":
                    self._unload_logic.update(bool(value))
            else:
                continue

            readings[name] = SensorReading(
                name=name,
                display_name=cfg.get("description", name),
                value=value,
                unit=unit,
                status=status,
                timestamp=datetime.now(),
            )

        return readings
