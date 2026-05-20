#!/usr/bin/env python3
"""
Отладочное окно — имитация сигналов датчиков.
Запуск: python -m app.dev.debug_window  (независимо от основного приложения)

Пишет целевые значения в общий JSON-файл, который читает MockSensors.
Основное приложение не знает о существовании этого модуля.
"""
import json
import sys
import tempfile
from pathlib import Path

import yaml
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

MOCK_STATE_FILE = Path(tempfile.gettempdir()) / "don1500b_mock.json"
CONFIG_FILE = Path(__file__).parent.parent.parent / "config.yaml"

_NAMES_RU = {
    "drum":        "Барабан",
    "kolosa":      "Колоса",
    "solomotryas": "Соломотряс",
    "fan_speed":   "Вентилятор",
    "bin_level":   "Бункер",
}


def _load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _read_state() -> dict:
    try:
        return json.loads(MOCK_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


class _SensorSlider(QWidget):
    def __init__(self, name: str, display: str, nominal: int, initial: int, max_rpm: int):
        super().__init__()
        self.name = name
        self._nominal = nominal

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(10)

        lbl = QLabel(display)
        lbl.setFixedWidth(110)
        row.addWidget(lbl)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, max_rpm)
        self._slider.setValue(initial)
        self._slider.setTickInterval(max_rpm // 10)
        self._slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        row.addWidget(self._slider, stretch=1)

        self._lbl_value = QLabel()
        self._lbl_value.setFixedWidth(96)
        self._lbl_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self._lbl_value)

        self._slider.valueChanged.connect(self._on_change)
        self._on_change(initial)

    def _on_change(self, value: int):
        self._lbl_value.setText(f"{value} об/мин")

    def value(self) -> int:
        return self._slider.value()

    def reset_to_nominal(self):
        self._slider.setValue(self._nominal)

    def set_zero(self):
        self._slider.setValue(0)

    # Forward signal so DebugWindow can connect to it
    @property
    def valueChanged(self):
        return self._slider.valueChanged


class DebugWindow(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self._sliders: dict[str, _SensorSlider] = {}
        self._checkboxes: dict[str, QCheckBox] = {}

        # Debounce timer — пишет в файл через 40 мс после последнего изменения
        self._write_timer = QTimer(self)
        self._write_timer.setSingleShot(True)
        self._write_timer.setInterval(40)
        self._write_timer.timeout.connect(self._flush)

        self.setWindowTitle("Отладка — Дон 1500б")
        self.setMinimumWidth(500)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        sensors = config.get("sensors", {}).get("list", {})
        current = _read_state()

        # ── Impulse sensors ────────────────────────────────────────────────
        group_impulse = QGroupBox("Импульсные датчики")
        vbox = QVBoxLayout(group_impulse)

        for name, cfg in sensors.items():
            if cfg.get("type") != "impulse":
                continue
            display = _NAMES_RU.get(name, name)
            nominal = int(cfg.get("nominal_rpm", 500))
            warn_high = int(cfg.get("warn_high", nominal * 2))
            max_rpm = int(warn_high * 1.6)
            initial = int(current.get(name, nominal))

            slider = _SensorSlider(name, display, nominal, initial, max_rpm)
            slider.valueChanged.connect(self._schedule_write)
            vbox.addWidget(slider)
            self._sliders[name] = slider

        root.addWidget(group_impulse)

        # ── Discrete sensors ───────────────────────────────────────────────
        group_discrete = QGroupBox("Дискретные датчики")
        vbox2 = QVBoxLayout(group_discrete)

        for name, cfg in sensors.items():
            if cfg.get("type") != "discrete":
                continue
            display = _NAMES_RU.get(name, name)
            cb = QCheckBox(display)
            cb.setChecked(bool(current.get(name, False)))
            cb.stateChanged.connect(self._schedule_write)
            vbox2.addWidget(cb)
            self._checkboxes[name] = cb

        root.addWidget(group_discrete)

        # ── Buttons ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()

        btn_nominal = QPushButton("↺  К номинальным")
        btn_nominal.setToolTip("Вернуть все датчики к номинальным значениям из config.yaml")
        btn_nominal.clicked.connect(self._reset_all)
        btn_row.addWidget(btn_nominal)

        btn_stop = QPushButton("■  Стоп всё")
        btn_stop.setToolTip("Установить 0 об/мин — имитация остановки")
        btn_stop.clicked.connect(self._stop_all)
        btn_row.addWidget(btn_stop)

        root.addLayout(btn_row)

        # ── Status ─────────────────────────────────────────────────────────
        lbl_file = QLabel(f"Файл: {MOCK_STATE_FILE}")
        lbl_file.setStyleSheet("color: #888; font-size: 11px;")
        lbl_file.setWordWrap(True)
        root.addWidget(lbl_file)

        self.adjustSize()
        self._flush()  # write initial state immediately

    # ── Internal ───────────────────────────────────────────────────────────

    def _schedule_write(self, *_):
        self._write_timer.start()

    def _flush(self):
        state = {name: s.value() for name, s in self._sliders.items()}
        state.update({name: cb.isChecked() for name, cb in self._checkboxes.items()})
        MOCK_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    def _reset_all(self):
        for s in self._sliders.values():
            s.reset_to_nominal()
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def _stop_all(self):
        for s in self._sliders.values():
            s.set_zero()


def main():
    config = _load_config()
    app = QApplication(sys.argv)
    window = DebugWindow(config)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
