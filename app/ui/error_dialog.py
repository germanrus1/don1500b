from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.sensors.sensor_base import SensorReading, SensorStatus
from app.ui.icons import sensor_icon

_SENSOR_NAMES_RU = {
    "drum":        "Барабан",
    "kolosa":      "Колоса",
    "solomotryas": "Соломотряс",
    "fan_speed":   "Вентилятор",
    "bin_level":   "Бункер",
}
_STATUS_TEXT = {
    SensorStatus.CRITICAL: "Критическая ошибка — значение близко к нулю",
    SensorStatus.WARN_LOW:  "Значение ниже нормы",
    SensorStatus.WARN_HIGH: "Значение выше нормы",
}


class ErrorDialog(QDialog):
    def __init__(
        self,
        reading: SensorReading,
        color: str,
        config,
        parent=None,
    ):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setFixedSize(460, 300)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        from app.ui.styles import build_stylesheet
        theme = config.ui.get("theme", "light")
        self.setStyleSheet(build_stylesheet(config, theme) + _DIALOG_EXTRA)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # ── Header: icon + sensor name ─────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(14)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(sensor_icon(reading.name, QColor(color), 52))
        icon_lbl.setFixedSize(56, 56)
        header.addWidget(icon_lbl)

        name_lbl = QLabel(_SENSOR_NAMES_RU.get(reading.name, reading.name))
        name_lbl.setObjectName("menuPageTitle")
        header.addWidget(name_lbl)
        header.addStretch()
        layout.addLayout(header)

        # ── Description ────────────────────────────────────────────────────
        status_line = _STATUS_TEXT.get(reading.status, "Ошибка датчика")
        desc = QLabel(f"{status_line}\n\nТекущее значение: {int(reading.value)} {reading.unit}")
        desc.setObjectName("errorDescText")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        # ── Large close button ─────────────────────────────────────────────
        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(56)
        close_btn.setObjectName("menuNavBtn")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._center_on_parent(parent)

    def _center_on_parent(self, parent):
        if parent is None:
            return
        px = parent.mapToGlobal(parent.rect().topLeft())
        self.move(
            px.x() + (parent.width()  - self.width())  // 2,
            px.y() + (parent.height() - self.height()) // 2,
        )


_DIALOG_EXTRA = """
QDialog {
    background-color: #2D2D2D;
    border: 2px solid #555555;
    border-radius: 10px;
}
QLabel#menuPageTitle { color: #FFFFFF; }
QLabel#errorDescText  { color: #DDDDDD; font-size: 15px; }
QPushButton#menuNavBtn {
    background-color: #3A3A3A;
    color: #FFFFFF;
    border: 2px solid #666666;
    border-radius: 8px;
    font-size: 17px;
}
QPushButton#menuNavBtn:hover { background-color: #4A4A4A; }
"""
