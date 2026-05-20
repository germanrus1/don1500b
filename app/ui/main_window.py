from datetime import datetime
from typing import Dict

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.config.config_loader import ConfigLoader
from app.logger.data_logger import DataLogger
from app.sensors.sensor_base import SensorReading, SensorStatus
from app.ui.styles import build_stylesheet


_DISPLAY_SENSORS = ["drum", "kolosa", "fan_speed"]

_SENSOR_NAMES_RU = {
    "drum": "Барабан",
    "kolosa": "Колоса",
    "fan_speed": "Вентилятор",
    "solomotryas": "Соломотряс",
    "soломotryas": "Соломотряс",
    "bin_level": "Бункер",
}

_STATUS_TEXT = {
    SensorStatus.CRITICAL: "Критическая ошибка — значение близко к нулю",
    SensorStatus.WARN_LOW: "Значение ниже нормы",
    SensorStatus.WARN_HIGH: "Значение выше нормы",
}


class MainWindow(QMainWindow):
    def __init__(self, config: ConfigLoader, logger: DataLogger):
        super().__init__()
        self._config = config
        self._logger = logger
        self._theme = config.ui.get("theme", "light")
        self._culture = "пшеница"
        self._unload_count = 0
        self._prev_statuses: Dict[str, SensorStatus] = {}

        self._setup_ui()
        self._apply_theme(self._theme)
        self._start_clock()

    # ── UI construction ────────────────────────────────────────────────────

    def _setup_ui(self):
        res = self._config.ui.get("resolution", {})
        w, h = res.get("width", 1200), res.get("height", 600)
        self.setFixedSize(w, h)
        self.setWindowTitle("Дон 1500б")

        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self._build_top_bar())

        body = QWidget()
        hbox = QHBoxLayout(body)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)
        hbox.addWidget(self._build_center_panel(), stretch=1)
        hbox.addWidget(self._build_right_panel())
        vbox.addWidget(body, stretch=1)

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topBar")
        bar.setFixedHeight(55)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)

        self._btn_menu = QPushButton("МЕНЮ")
        self._btn_menu.setObjectName("btnMenu")
        self._btn_menu.setFixedSize(110, 38)
        layout.addWidget(self._btn_menu)

        layout.addStretch()

        self._lbl_time = QLabel()
        self._lbl_time.setObjectName("labelTime")
        self._lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._lbl_time)

        layout.addStretch()

        # Balancing spacer so time stays centered
        spacer = QWidget()
        spacer.setFixedWidth(110)
        layout.addWidget(spacer)

        return bar

    def _build_center_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panelCenter")

        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(24, 0, 24, 0)
        vbox.addStretch(2)

        # Row of error icons
        icons_wrap = QWidget()
        self._icons_layout = QHBoxLayout(icons_wrap)
        self._icons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icons_layout.setSpacing(20)
        self._icons_layout.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(icons_wrap, alignment=Qt.AlignmentFlag.AlignHCenter)

        vbox.addSpacing(16)

        # Error description box (hidden by default)
        self._desc_box = QFrame()
        self._desc_box.setObjectName("errorDescBox")
        self._desc_box.setVisible(False)
        self._desc_box.setFixedWidth(480)

        dl = QVBoxLayout(self._desc_box)
        dl.setContentsMargins(16, 12, 16, 12)
        dl.setSpacing(6)

        header = QHBoxLayout()
        self._desc_title = QLabel()
        self._desc_title.setObjectName("errorDescTitle")
        header.addWidget(self._desc_title)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("errorDescClose")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(lambda: self._desc_box.setVisible(False))
        header.addWidget(close_btn)
        dl.addLayout(header)

        self._desc_text = QLabel()
        self._desc_text.setObjectName("errorDescText")
        self._desc_text.setWordWrap(True)
        dl.addWidget(self._desc_text)

        vbox.addWidget(self._desc_box, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox.addStretch(3)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panelRight")
        panel.setFixedWidth(280)

        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(20, 24, 20, 24)
        vbox.setSpacing(0)

        self._sensor_value_labels: Dict[str, QLabel] = {}

        for i, name in enumerate(_DISPLAY_SENSORS):
            if i > 0:
                sep = QWidget()
                sep.setObjectName("sensorSep")
                sep.setFixedHeight(1)
                vbox.addWidget(sep)
                vbox.addSpacing(14)

            lbl_name = QLabel(_SENSOR_NAMES_RU.get(name, name))
            lbl_name.setObjectName("sensorLabel")
            vbox.addWidget(lbl_name)

            lbl_value = QLabel("—")
            lbl_value.setObjectName("sensorValue")
            vbox.addWidget(lbl_value)
            vbox.addSpacing(10)

            self._sensor_value_labels[name] = lbl_value

        vbox.addStretch()
        return panel

    # ── Clock ──────────────────────────────────────────────────────────────

    def _start_clock(self):
        timer = QTimer(self)
        timer.timeout.connect(self._tick_clock)
        timer.start(1000)
        self._tick_clock()

    def _tick_clock(self):
        fmt = self._config.interface.get("time_format", "%H:%M:%S")
        self._lbl_time.setText(datetime.now().strftime(fmt))

    # ── Slots ──────────────────────────────────────────────────────────────

    @pyqtSlot(dict)
    def update_sensors(self, readings: Dict[str, SensorReading]):
        # Right panel values
        for name, lbl in self._sensor_value_labels.items():
            r = readings.get(name)
            lbl.setText(f"{int(r.value)} {r.unit}" if r else "—")

        # Error icons
        errors = [r for r in readings.values() if r.has_error]
        self._refresh_error_icons(errors)

        # Log only status changes
        for name, reading in readings.items():
            prev = self._prev_statuses.get(name)
            if prev != reading.status:
                self._logger.log_reading(name, reading.value, reading.unit, reading.status.value)
                self._prev_statuses[name] = reading.status

    @pyqtSlot(int)
    def on_unload(self, count: int):
        self._unload_count = count
        self._logger.log_unload(count, self._culture)

    # ── Error icons ────────────────────────────────────────────────────────

    def _refresh_error_icons(self, errors: list):
        while self._icons_layout.count():
            w = self._icons_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self._icons_layout.parentWidget().setVisible(bool(errors))

        c = self._config.ui.get(
            "colors_dark" if self._theme == "dark" else "colors_light", {}
        )

        for reading in errors:
            is_crit = reading.status == SensorStatus.CRITICAL
            color = c.get("error_critical" if is_crit else "error_warning",
                          "#E63946" if is_crit else "#F77F00")

            icon = QLabel("⚠")
            icon.setStyleSheet(
                f"font-size: 52px; color: {color}; background: transparent;"
            )
            icon.setCursor(Qt.CursorShape.PointingHandCursor)
            icon.setToolTip(_SENSOR_NAMES_RU.get(reading.name, reading.name))

            # Capture reading in closure
            icon.mousePressEvent = lambda _e, r=reading: self._show_error_desc(r)

            self._icons_layout.addWidget(icon)

    def _show_error_desc(self, reading: SensorReading):
        name_ru = _SENSOR_NAMES_RU.get(reading.name, reading.name)
        status_line = _STATUS_TEXT.get(reading.status, "Ошибка датчика")

        self._desc_title.setText(f"⚠  {name_ru}")
        self._desc_text.setText(
            f"{status_line}\n"
            f"Текущее значение: {int(reading.value)} {reading.unit}"
        )
        self._desc_box.setVisible(True)

    # ── Theme ──────────────────────────────────────────────────────────────

    def _apply_theme(self, theme: str):
        self._theme = theme
        self.setStyleSheet(build_stylesheet(self._config, theme))

    def toggle_theme(self):
        self._apply_theme("dark" if self._theme == "light" else "light")
