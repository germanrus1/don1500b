import json
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Dict


MOCK_STATE_FILE = Path(tempfile.gettempdir()) / "don1500b_mock.json"


class MockSensors:
    """
    Simulates GPIO for dev mode.
    Reads target RPM values from a shared JSON file so the debug window
    can control them without knowing about the main app.
    """

    def __init__(self, sensors_config: dict):
        self._cfg = sensors_config
        self._pulse_callbacks: Dict[str, Callable] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._write_initial_state()

    def _write_initial_state(self):
        if MOCK_STATE_FILE.exists():
            return
        state: dict = {}
        for name, cfg in self._cfg.items():
            if cfg.get("type") == "impulse":
                state[name] = cfg.get("nominal_rpm", 0)
            elif cfg.get("type") == "discrete":
                state[name] = False
        MOCK_STATE_FILE.write_text(json.dumps(state), encoding="utf-8")

    def read_state(self) -> dict:
        try:
            return json.loads(MOCK_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def register_pulse_callback(self, sensor_name: str, callback: Callable):
        self._pulse_callbacks[sensor_name] = callback

    def get_discrete_value(self, sensor_name: str) -> bool:
        return bool(self.read_state().get(sensor_name, False))

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="MockSensors")
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        last_pulse: Dict[str, float] = {}

        while self._running:
            now = time.monotonic()
            state = self.read_state()

            for name, callback in self._pulse_callbacks.items():
                rpm = float(state.get(name, 0))
                if rpm <= 0:
                    continue

                interval = 60.0 / rpm
                last = last_pulse.get(name, now - interval)
                pulses_due = int((now - last) / interval)

                if pulses_due > 0:
                    for _ in range(min(pulses_due, 10)):
                        callback()
                    last_pulse[name] = last + pulses_due * interval

            time.sleep(0.005)
