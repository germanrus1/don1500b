from datetime import datetime
from typing import Dict

from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer, pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config.config_loader import ConfigLoader
from app.logger.data_logger import DataLogger
from app.sensors.sensor_base import SensorReading, SensorStatus
from app.ui.error_dialog import ErrorDialog
from app.ui.icons import sensor_icon, sensor_icon_badge
from app.ui.menu_dialog import MenuDialog
from app.ui.styles import build_stylesheet


_DISPLAY_SENSORS = ["drum", "kolosa", "fan_speed"]

_SENSOR_NAMES_RU = {
    "drum":        "Барабан",
    "kolosa":      "Колоса",
    "fan_speed":   "Вентилятор",
    "solomotryas": "Соломотряс",
    "bin_level":   "Бункер",
}

_PANEL_ICON_COLOR = "#27AE60"
_PANEL_ICON_SIZE  = 38
_RIGHT_PANEL_W    = 240
_TOP_BAR_H        = 55

_ICON_SIZE  = 64
_ICON_ROW_H = _ICON_SIZE + 8


class MainWindow(QMainWindow):
    def __init__(self, config: ConfigLoader, logger: DataLogger):
        super().__init__()
        self._config = config
        self._logger = logger
        self._theme = config.ui.get("theme", "light")
        self._culture = config.interface.get("cultures", ["Пшеница"])[0]
        self._unload_count = 0
        self._work_start = datetime.now()
        self._prev_statuses: Dict[str, SensorStatus] = {}

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
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
        self._btn_menu.clicked.connect(self._open_menu)
        layout.addWidget(self._btn_menu)

        layout.addStretch()

        # Center group: time + culture — kept together and centered as a unit
        center_w = QWidget()
        center_row = QHBoxLayout(center_w)
        center_row.setContentsMargins(0, 0, 0, 0)
        center_row.setSpacing(0)

        self._lbl_time = QLabel()
        self._lbl_time.setObjectName("labelTime")
        self._lbl_time.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        center_row.addWidget(self._lbl_time)

        center_row.addSpacing(18)

        self._lbl_culture = QLabel(self._culture)
        self._lbl_culture.setObjectName("labelCulture")
        self._lbl_culture.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        center_row.addWidget(self._lbl_culture)

        layout.addWidget(center_w)
        layout.addStretch()

        spacer = QWidget()
        spacer.setFixedWidth(110)
        layout.addWidget(spacer)

        return bar

    def _build_center_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panelCenter")

        # Absolutely positioned icon strip — geometry updated in resizeEvent
        self._icons_container = QWidget(panel)
        self._icons_container.setGeometry(0, 0, 0, _ICON_ROW_H)
        self._icons_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        icons_row = QHBoxLayout(self._icons_container)
        icons_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icons_row.setSpacing(20)
        icons_row.setContentsMargins(0, 0, 0, 0)
        self._icons_layout = icons_row

        self._icons_container.setVisible(False)
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panelRight")
        panel.setFixedWidth(_RIGHT_PANEL_W)

        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(20, 24, 20, 24)
        vbox.setSpacing(0)

        # Floating sensor-name toast — absolutely positioned, hidden by default
        self._sensor_toast = QLabel(panel)
        self._sensor_toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sensor_toast.setGeometry(16, 0, _RIGHT_PANEL_W - 32, 44)
        self._sensor_toast.setStyleSheet(
            "background-color: #2D2D2D; color: #FFFFFF;"
            "border-radius: 10px; font-size: 16px; font-weight: bold;"
        )
        self._sensor_toast.hide()

        self._toast_effect = QGraphicsOpacityEffect()
        self._sensor_toast.setGraphicsEffect(self._toast_effect)

        self._toast_in = QPropertyAnimation(self._toast_effect, b"opacity")
        self._toast_in.setDuration(180)
        self._toast_in.setStartValue(0.0)
        self._toast_in.setEndValue(1.0)

        self._toast_out = QPropertyAnimation(self._toast_effect, b"opacity")
        self._toast_out.setDuration(400)
        self._toast_out.setStartValue(1.0)
        self._toast_out.setEndValue(0.0)
        self._toast_out.finished.connect(self._sensor_toast.hide)

        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._toast_out.start)

        self._sensor_value_labels: Dict[str, QLabel] = {}

        for i, name in enumerate(_DISPLAY_SENSORS):
            if i > 0:
                sep = QWidget()
                sep.setObjectName("sensorSep")
                sep.setFixedHeight(1)
                vbox.addWidget(sep)
                vbox.addSpacing(14)

            row_w = QWidget()
            row_w.setCursor(Qt.CursorShape.PointingHandCursor)
            row_w.mousePressEvent = lambda _e, n=name, rw=row_w: self._show_sensor_toast(n, rw)

            row = QHBoxLayout(row_w)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)
            row.addStretch()

            lbl_value = QLabel("—")
            lbl_value.setObjectName("sensorValue")
            row.addWidget(lbl_value)

            lbl_icon = QLabel()
            lbl_icon.setPixmap(
                sensor_icon(name, QColor(_PANEL_ICON_COLOR), _PANEL_ICON_SIZE)
            )
            lbl_icon.setFixedSize(_PANEL_ICON_SIZE + 4, _PANEL_ICON_SIZE + 4)
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            lbl_icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            row.addWidget(lbl_icon)

            vbox.addWidget(row_w)
            vbox.addSpacing(10)

            self._sensor_value_labels[name] = lbl_value

        vbox.addStretch()
        return panel

    def _show_sensor_toast(self, name: str, row_widget: QWidget):
        self._toast_timer.stop()
        self._toast_out.stop()

        panel = self._sensor_toast.parent()
        toast_h = 44
        toast_w = panel.width() - 32
        row_top = row_widget.mapTo(panel, row_widget.rect().topLeft()).y()
        y = row_top - toast_h - 6
        if y < 4:
            y = row_top + row_widget.height() + 6
        self._sensor_toast.setGeometry(16, y, toast_w, toast_h)

        self._sensor_toast.setText(_SENSOR_NAMES_RU.get(name, name))
        self._sensor_toast.show()
        self._sensor_toast.raise_()
        self._toast_in.stop()
        self._toast_in.start()
        self._toast_timer.start(1800)

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
        for name, lbl in self._sensor_value_labels.items():
            r = readings.get(name)
            lbl.setText(f"{int(r.value)}" if r else "—")

        errors = [r for r in readings.values() if r.has_error]
        self._refresh_error_icons(errors)

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

        self._icons_container.setVisible(bool(errors))
        if not errors:
            return

        c = self._config.ui.get(
            "colors_dark" if self._theme == "dark" else "colors_light", {}
        )

        for reading in errors:
            is_crit = reading.status == SensorStatus.CRITICAL
            color_hex = c.get(
                "error_critical" if is_crit else "error_warning",
                "#E63946" if is_crit else "#F77F00",
            )

            icon_lbl = QLabel()
            icon_lbl.setPixmap(sensor_icon_badge(reading.name, QColor(color_hex), _ICON_SIZE))
            icon_lbl.setFixedSize(_ICON_SIZE + 4, _ICON_SIZE + 4)
            icon_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            icon_lbl.setToolTip(_SENSOR_NAMES_RU.get(reading.name, reading.name))
            icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            icon_lbl.mousePressEvent = (
                lambda _e, r=reading, col=color_hex: self._open_error_dialog(r, col)
            )

            self._icons_layout.addWidget(icon_lbl)

    def _open_error_dialog(self, reading: SensorReading, color: str):
        dlg = ErrorDialog(reading, color, self._config, parent=self)
        dlg.exec()

    # ── Theme / culture ────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_initial_mode_applied", False):
            self._initial_mode_applied = True
            if self._config.ui.get("window_mode", "windowed") == "fullscreen":
                self.showFullScreen()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "_icons_container"):
            return
        pw = self.width() - _RIGHT_PANEL_W
        ph = self.height() - _TOP_BAR_H
        bottom_pad = max(12, int(ph * 0.035))
        self._icons_container.setGeometry(
            0, ph - _ICON_ROW_H - bottom_pad, pw, _ICON_ROW_H
        )

    def _set_window_mode(self, mode: str):
        if mode == "fullscreen":
            self.showFullScreen()
        else:
            self.showNormal()

    def _apply_theme(self, theme: str):
        self._theme = theme
        self.setStyleSheet(build_stylesheet(self._config, theme))

    def _set_culture(self, culture: str):
        self._culture = culture
        self._lbl_culture.setText(culture)

    def _open_menu(self):
        stats = {
            "unload_count": self._unload_count,
            "culture":      self._culture,
            "work_start":   self._work_start,
        }
        dialog = MenuDialog(
            self._config, stats, self._logger,
            current_theme=self._theme, parent=self,
        )
        dialog.theme_changed.connect(self._apply_theme)
        dialog.culture_changed.connect(self._set_culture)
        dialog.window_mode_changed.connect(self._set_window_mode)
        dialog.exec()
