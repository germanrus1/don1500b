from datetime import datetime
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
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
from app.ui.menu_dialog import MenuDialog
from app.ui.speedometer import Speedometer
from app.ui.styles import build_stylesheet, get_tokens

try:
    import qtawesome as qta
    _HAS_QTA = True
except Exception:
    _HAS_QTA = False


# ── Sensor display model ───────────────────────────────────────────────────

_LEFT_SENSORS: List[dict] = [
    {"id": "erpm",  "short": "Двигатель",     "full": "Обороты двигателя",                "unit": "об/мин", "mdi": "mdi.cog",              "color": "#7c5cf0"},
    {"id": "etemp", "short": "Темп. двигат.", "full": "Температура охлаждающей жидкости", "unit": "°C",     "mdi": "mdi.thermometer",       "color": "#e85d3a"},
    {"id": "oil",   "short": "Давл. масла",   "full": "Давление масла в двигателе",       "unit": "бар",    "mdi": "mdi.gauge",             "color": "#5b6ef0"},
    {"id": "fuel",  "short": "Топливо",       "full": "Уровень топлива в баке",           "unit": "%",      "mdi": "mdi.gas-station",       "color": "#f0871a"},
    {"id": "volt",  "short": "Бортсеть",      "full": "Напряжение бортовой сети",         "unit": "В",      "mdi": "mdi.lightning-bolt",    "color": "#e0930f"},
]
_RIGHT_SENSORS: List[dict] = [
    {"id": "drum",  "short": "Барабан",       "full": "Частота молотильного барабана",    "unit": "об/мин", "mdi": "mdi.rotate-3d-variant", "color": "#3b82f6"},
    {"id": "auger", "short": "Колос. шнек",  "full": "Обороты колосового шнека",         "unit": "об/мин", "mdi": "mdi.swap-horizontal",   "color": "#22a05a"},
    {"id": "fan",   "short": "Вентилятор",    "full": "Вентилятор системы очистки",       "unit": "об/мин", "mdi": "mdi.fan",               "color": "#0ea5b5"},
    {"id": "moist", "short": "Влажность",     "full": "Влажность зерна",                  "unit": "%",      "mdi": "mdi.water",             "color": "#14a08a"},
    {"id": "loss",  "short": "Потери зерна",  "full": "Потери зерна за молотилкой",       "unit": "%",      "mdi": "mdi.grain",             "color": "#d6479b"},
]
_ALL_SENSORS = _LEFT_SENSORS + _RIGHT_SENSORS

# Hardware sensor name → display ID
_ALIAS: Dict[str, str] = {
    "drum":      "drum",
    "kolosa":    "auger",
    "fan_speed": "fan",
}

_COL_W   = 232
_TOP_H   = 55
_COL_PAD = 12
_CHIP_SZ = 46
_ICON_SZ = 27
_CHIP_R  = 11


# ── Helpers ────────────────────────────────────────────────────────────────

def _fmt(v: float) -> str:
    return str(int(v)) if v == int(v) else f"{v:.1f}"


def _chip_pixmap(mdi: str, color_hex: str, is_dark: bool) -> QPixmap:
    color = QColor(color_hex)
    alpha = int(255 * (0.22 if is_dark else 0.15))
    bg    = QColor(color.red(), color.green(), color.blue(), alpha)

    px = QPixmap(_CHIP_SZ, _CHIP_SZ)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(bg))
    p.drawRoundedRect(0, 0, _CHIP_SZ, _CHIP_SZ, _CHIP_R, _CHIP_R)
    if _HAS_QTA:
        try:
            icon_px = qta.icon(mdi, color=color_hex).pixmap(_ICON_SZ, _ICON_SZ)
            off = (_CHIP_SZ - _ICON_SZ) // 2
            p.drawPixmap(off, off, icon_px)
        except Exception:
            pass
    p.end()
    return px


def _fault_circle_pixmap(mdi: str, color_hex: str, size: int = 64) -> QPixmap:
    color = QColor(color_hex)
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    p.drawEllipse(0, 0, size, size)
    if _HAS_QTA:
        try:
            icon_px = qta.icon(mdi, color="#ffffff").pixmap(34, 34)
            off = (size - 34) // 2
            p.drawPixmap(off, off, icon_px)
        except Exception:
            pass
    p.end()
    return px


# ── Sensor card widget ─────────────────────────────────────────────────────

class _SensorCard(QFrame):
    tapped = pyqtSignal(str)  # full sensor name

    def __init__(self, sensor: dict, tokens: dict, is_dark: bool, parent=None):
        super().__init__(parent)
        self._sensor  = sensor
        self._tokens  = tokens
        self._is_dark = is_dark
        self._state   = ""
        self.setObjectName("sensorCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build(tokens, is_dark)

    def _build(self, tokens: dict, is_dark: bool):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(_COL_PAD, 0, _COL_PAD, 0)
        hl.setSpacing(12)

        self._chip_lbl = QLabel()
        self._chip_lbl.setFixedSize(_CHIP_SZ, _CHIP_SZ)
        self._chip_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._chip_lbl.setPixmap(_chip_pixmap(self._sensor["mdi"], self._sensor["color"], is_dark))
        hl.addWidget(self._chip_lbl)

        text_w = QWidget()
        text_w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        vl = QVBoxLayout(text_w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(1)
        vl.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._name_lbl = QLabel(self._sensor["short"])
        self._name_lbl.setObjectName("cardName")
        vl.addWidget(self._name_lbl)

        val_row = QWidget()
        val_row.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        vr = QHBoxLayout(val_row)
        vr.setContentsMargins(0, 0, 0, 0)
        vr.setSpacing(5)
        vr.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self._val_lbl  = QLabel("—")
        self._val_lbl.setObjectName("cardValue")
        vr.addWidget(self._val_lbl)

        self._unit_lbl = QLabel(self._sensor["unit"])
        self._unit_lbl.setObjectName("cardUnit")
        self._unit_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
        vr.addWidget(self._unit_lbl)
        vr.addStretch()

        vl.addWidget(val_row)
        hl.addWidget(text_w, stretch=1)

    def mousePressEvent(self, event):
        self.tapped.emit(self._sensor["full"])
        super().mousePressEvent(event)

    def update_value(self, value: Optional[float], state: str, tokens: dict):
        self._state  = state
        self._tokens = tokens
        crit = tokens.get("error_critical", "#d92d20")
        warn = tokens.get("error_warning",  "#e8830c")
        fg   = tokens.get("text_primary",   "#192230")

        display = _fmt(value) if value is not None else "—"
        self._val_lbl.setText(display)

        if state == "critical":
            val_color   = crit
            card_border = f"2px solid {crit}"
        elif state == "warning":
            val_color   = warn
            card_border = f"2px solid {warn}"
        else:
            val_color   = fg
            card_border = f"1px solid {tokens.get('border', '#e1e6ee')}"

        surface = tokens.get("surface", "#ffffff")
        self.setStyleSheet(
            f"QFrame#sensorCard {{ background-color: {surface}; border: {card_border}; border-radius: 16px; }}"
        )
        self._val_lbl.setStyleSheet(
            f"font-family: 'IBM Plex Mono', 'Courier New', monospace; "
            f"font-size: 31px; font-weight: 700; color: {val_color}; background: transparent;"
        )


# ── Main window ────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, config: ConfigLoader, logger: DataLogger, collector=None):
        super().__init__()
        self._config       = config
        self._logger       = logger
        self._collector    = collector
        self._theme        = config.ui.get("theme", "light")
        self._culture      = config.interface.get("cultures", ["Пшеница"])[0]
        self._unload_count = 0
        self._work_start   = datetime.now()
        self._speed        = 0.0
        self._cards: Dict[str, _SensorCard] = {}
        self._prev_readings: Dict[str, SensorReading] = {}

        mode = config.ui.get("window_mode", "windowed")
        flags = Qt.WindowType.FramelessWindowHint if mode == "fullscreen" else Qt.WindowType.Window
        self.setWindowFlags(flags)
        self._setup_ui()
        self._apply_theme(self._theme)
        self._start_clock()

    # ── Build UI ───────────────────────────────────────────────────────────

    def _setup_ui(self):
        res  = self._config.ui.get("resolution", {})
        w, h = res.get("width", 1024), res.get("height", 600)
        self.setFixedSize(w, h)
        self.setWindowTitle("Дон 1500б")

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_top_bar())

        body = QWidget()
        body_hl = QHBoxLayout(body)
        body_hl.setContentsMargins(0, 0, 0, 0)
        body_hl.setSpacing(0)

        self._left_col_w = self._build_sensor_column(_LEFT_SENSORS, "left")
        body_hl.addWidget(self._left_col_w)

        div_l = QFrame()
        div_l.setObjectName("divider")
        div_l.setFixedWidth(1)
        body_hl.addWidget(div_l)

        body_hl.addWidget(self._build_center_panel(), stretch=1)

        div_r = QFrame()
        div_r.setObjectName("divider")
        div_r.setFixedWidth(1)
        body_hl.addWidget(div_r)

        self._right_col_w = self._build_sensor_column(_RIGHT_SENSORS, "right")
        body_hl.addWidget(self._right_col_w)

        root.addWidget(body, stretch=1)

        # Floating toast overlay on central widget
        self._toast_lbl = QLabel(central)
        self._toast_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toast_lbl.setStyleSheet(
            "background-color: #1c1e24; color: #ffffff; border-radius: 10px;"
            "font-size: 14px; font-weight: 600; padding: 9px 14px;"
        )
        self._toast_lbl.hide()

        self._toast_effect = QGraphicsOpacityEffect()
        self._toast_lbl.setGraphicsEffect(self._toast_effect)
        self._toast_anim_in  = QPropertyAnimation(self._toast_effect, b"opacity")
        self._toast_anim_in.setDuration(160)
        self._toast_anim_in.setStartValue(0.0)
        self._toast_anim_in.setEndValue(1.0)
        self._toast_anim_out = QPropertyAnimation(self._toast_effect, b"opacity")
        self._toast_anim_out.setDuration(400)
        self._toast_anim_out.setStartValue(1.0)
        self._toast_anim_out.setEndValue(0.0)
        self._toast_anim_out.finished.connect(self._toast_lbl.hide)
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._toast_anim_out.start)

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topBar")
        bar.setFixedHeight(_TOP_H)

        hl = QHBoxLayout(bar)
        hl.setContentsMargins(14, 0, 14, 0)
        hl.setSpacing(0)

        # Left: МЕНЮ pill
        self._btn_menu = QPushButton("  Меню")
        self._btn_menu.setObjectName("btnMenu")
        self._btn_menu.setFixedSize(130, 42)
        self._btn_menu.clicked.connect(self._open_menu)
        if _HAS_QTA:
            try:
                self._btn_menu.setIcon(qta.icon("mdi.menu", color="#ffffff"))
            except Exception:
                pass
        hl.addWidget(self._btn_menu, 0, Qt.AlignmentFlag.AlignVCenter)
        hl.addStretch(1)

        # Center: clock
        self._lbl_time = QLabel()
        self._lbl_time.setObjectName("labelTime")
        self._lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(self._lbl_time, 0, Qt.AlignmentFlag.AlignVCenter)
        hl.addStretch(1)

        # Right: culture name + chip
        crop_w = QWidget()
        crop_hl = QHBoxLayout(crop_w)
        crop_hl.setContentsMargins(0, 0, 0, 0)
        crop_hl.setSpacing(9)

        name_col = QWidget()
        name_vl  = QVBoxLayout(name_col)
        name_vl.setContentsMargins(0, 0, 0, 0)
        name_vl.setSpacing(1)

        caption = QLabel("КУЛЬТУРА")
        caption.setObjectName("labelCropCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignRight)
        name_vl.addWidget(caption)

        self._lbl_culture = QLabel(self._culture)
        self._lbl_culture.setObjectName("labelCropName")
        self._lbl_culture.setAlignment(Qt.AlignmentFlag.AlignRight)
        name_vl.addWidget(self._lbl_culture)

        crop_hl.addWidget(name_col)

        chip = QLabel()
        chip.setFixedSize(34, 34)
        chip.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip.setPixmap(self._crop_chip_pixmap())
        self._crop_chip = chip
        crop_hl.addWidget(chip)

        hl.addWidget(crop_w, 0, Qt.AlignmentFlag.AlignVCenter)
        return bar

    def _crop_chip_pixmap(self) -> QPixmap:
        size = 34
        px   = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        bg = QColor(0x22, 0xa0, 0x5a, 40)
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(0, 0, size, size, 10, 10)
        if _HAS_QTA:
            try:
                icon_px = qta.icon("mdi.leaf", color="#22a05a").pixmap(22, 22)
                p.drawPixmap((size - 22) // 2, (size - 22) // 2, icon_px)
            except Exception:
                pass
        p.end()
        return px

    def _build_sensor_column(self, sensors: List[dict], side: str) -> QWidget:
        col = QWidget()
        col.setObjectName("sensorColumn")
        col.setFixedWidth(_COL_W)

        vl = QVBoxLayout(col)
        vl.setContentsMargins(_COL_PAD, _COL_PAD, _COL_PAD, _COL_PAD)
        vl.setSpacing(10)

        tokens  = get_tokens(self._config, self._theme)
        is_dark = self._theme == "dark"

        for s in sensors:
            card = _SensorCard(s, tokens, is_dark, parent=col)
            card.tapped.connect(lambda name, c=card: self._show_toast(name, c, side))
            vl.addWidget(card, stretch=1)
            self._cards[s["id"]] = card

        return col

    def _build_center_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("panelCenter")

        vl = QVBoxLayout(panel)
        vl.setContentsMargins(18, 14, 18, 14)
        vl.setSpacing(22)
        vl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self._speedometer = Speedometer()
        vl.addWidget(self._speedometer, 0, Qt.AlignmentFlag.AlignHCenter)

        # Fault strip — only shown when there are active errors
        self._status_area = QWidget()
        self._status_area.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._status_area.hide()
        self._status_hl   = QHBoxLayout(self._status_area)
        self._status_hl.setContentsMargins(0, 0, 0, 0)
        self._status_hl.setSpacing(26)
        self._status_hl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        vl.addWidget(self._status_area, 0, Qt.AlignmentFlag.AlignHCenter)

        self._fault_widgets: List[QWidget] = []
        return panel

    # ── Fault strip ────────────────────────────────────────────────────────

    def _refresh_fault_strip(self, faults: List[SensorReading]):
        # Remove previous fault buttons
        for fw in self._fault_widgets:
            fw.hide()
            self._status_hl.removeWidget(fw)
            fw.deleteLater()
        self._fault_widgets.clear()

        tokens  = get_tokens(self._config, self._theme)
        has_err = bool(faults)
        self._status_area.setVisible(has_err)

        for reading in faults:
            s_def = next((s for s in _ALL_SENSORS
                          if s["id"] == _ALIAS.get(reading.name, reading.name)), None)
            if s_def is None:
                continue

            is_crit = reading.status == SensorStatus.CRITICAL
            color   = tokens["error_critical"] if is_crit else tokens["error_warning"]
            px      = _fault_circle_pixmap(s_def["mdi"], color)

            container = QWidget()
            container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            cvl = QVBoxLayout(container)
            cvl.setContentsMargins(0, 0, 0, 0)
            cvl.setSpacing(7)
            cvl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(64, 64)
            icon_lbl.setPixmap(px)
            icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            icon_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            icon_lbl.mousePressEvent = (
                lambda _e, r=reading, c=color: self._open_error_dialog(r, c)
            )
            cvl.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignHCenter)

            cap_lbl = QLabel(s_def["short"])
            cap_lbl.setObjectName("cardName")
            cap_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            cvl.addWidget(cap_lbl, 0, Qt.AlignmentFlag.AlignHCenter)

            self._status_hl.addWidget(container)
            self._fault_widgets.append(container)

    # ── Toast ──────────────────────────────────────────────────────────────

    def _show_toast(self, full_name: str, card: _SensorCard, side: str):
        self._toast_timer.stop()
        self._toast_anim_out.stop()

        self._toast_lbl.setText(full_name)
        self._toast_lbl.adjustSize()

        # Position: center y of card, between column and center panel
        card_center_y = card.mapTo(self.centralWidget(), card.rect().center()).y()
        tw = max(self._toast_lbl.sizeHint().width() + 28, 200)
        th = 38

        if side == "left":
            x = _COL_W + 8
        else:
            x = self.width() - _COL_W - 8 - tw

        self._toast_lbl.setGeometry(x, card_center_y - th // 2, tw, th)
        self._toast_lbl.show()
        self._toast_lbl.raise_()
        self._toast_anim_in.stop()
        self._toast_anim_in.start()
        self._toast_timer.start(2200)

    # ── Clock ──────────────────────────────────────────────────────────────

    def _start_clock(self):
        t = QTimer(self)
        t.timeout.connect(self._tick_clock)
        t.start(1000)
        self._tick_clock()

    def _tick_clock(self):
        fmt = self._config.interface.get("time_format", "%H:%M:%S")
        self._lbl_time.setText(datetime.now().strftime(fmt))

    # ── Sensor updates ─────────────────────────────────────────────────────

    @pyqtSlot(dict)
    def update_sensors(self, readings: Dict[str, SensorReading]):
        tokens  = get_tokens(self._config, self._theme)
        faults: List[SensorReading] = []

        for hw_name, reading in readings.items():
            display_id = _ALIAS.get(hw_name)
            if display_id and display_id in self._cards:
                state = (
                    "critical" if reading.status == SensorStatus.CRITICAL
                    else "warning" if reading.has_error
                    else ""
                )
                self._cards[display_id].update_value(reading.value, state, tokens)

            if reading.has_error:
                faults.append(reading)

            prev = self._prev_readings.get(hw_name)
            if prev is None or prev.status != reading.status:
                self._logger.log_reading(hw_name, reading.value, reading.unit, reading.status.value)
            self._prev_readings[hw_name] = reading

        self._refresh_fault_strip(faults)

    @pyqtSlot(int)
    def on_unload(self, count: int):
        self._unload_count = count
        self._logger.log_unload(count, self._culture)

    # ── Error popup ────────────────────────────────────────────────────────

    def _open_error_dialog(self, reading: SensorReading, color: str):
        from app.ui.error_dialog import ErrorDialog
        dlg = ErrorDialog(reading, color, self._config, parent=self)
        dlg.exec()

    # ── Theme / culture ────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_init_mode_done", False):
            self._init_mode_done = True
            if self._config.ui.get("window_mode", "windowed") == "fullscreen":
                self.showFullScreen()

    def _set_window_mode(self, mode: str):
        self.hide()
        flags = (Qt.WindowType.FramelessWindowHint
                 if mode == "fullscreen" else Qt.WindowType.Window)
        self.setWindowFlags(flags)
        self.show()
        if mode == "fullscreen":
            self.showFullScreen()
        else:
            self.showNormal()

    def _apply_theme(self, theme: str):
        self._theme = theme
        self.setStyleSheet(build_stylesheet(self._config, theme))

        tokens  = get_tokens(self._config, theme)
        is_dark = theme == "dark"

        self._speedometer.apply_tokens(tokens)

        # Update chip pixmaps and base card appearance for all sensor cards
        for card in self._cards.values():
            card._chip_lbl.setPixmap(
                _chip_pixmap(card._sensor["mdi"], card._sensor["color"], is_dark)
            )
            # Reset to default state; will be re-colored by update_sensors below
            card._state = ""
            card.setStyleSheet("")

        # Re-apply last known values so value colors and borders are correct
        if self._prev_readings:
            self.update_sensors(self._prev_readings)

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
            collector=self._collector,
            current_theme=self._theme, parent=self,
        )
        dialog.theme_changed.connect(self._apply_theme)
        dialog.culture_changed.connect(self._set_culture)
        if self._collector is not None:
            dialog.culture_changed.connect(self._collector.set_culture)
        dialog.window_mode_changed.connect(self._set_window_mode)
        dialog.sensors_changed.connect(lambda: None)  # no-op; panel is design-fixed
        dialog.exec()
