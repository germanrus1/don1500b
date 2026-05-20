from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPixmap

_ICONS_DIR = Path(__file__).parent.parent.parent / "assets" / "icons"

_FILES = {
    "drum":        "drum.png",
    "kolosa":      "kolosa.png",
    "solomotryas": "solomotryas.png",
    "fan_speed":   "fan_speed.png",
    "bin_level":   "bin_level.png",
}


def sensor_icon(sensor_name: str, color: QColor, size: int = 52) -> QPixmap:
    """Monochrome icon tinted with color — for status panels."""
    path = _ICONS_DIR / _FILES.get(sensor_name, "drum.png")
    src = QPixmap(str(path))
    if src.isNull():
        return _fallback_icon(color, size)
    src = src.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return _tint(src, color)


def sensor_icon_badge(sensor_name: str, bg_color: QColor, size: int = 64) -> QPixmap:
    """Colored rounded square with white icon centered — for error alerts."""
    path = _ICONS_DIR / _FILES.get(sensor_name, "drum.png")
    src = QPixmap(str(path))

    badge = QPixmap(size, size)
    badge.fill(Qt.GlobalColor.transparent)
    p = QPainter(badge)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    p.setBrush(QBrush(bg_color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(0, 0, size, size, size // 5, size // 5)

    if not src.isNull():
        inner = int(size * 0.62)
        icon = src.scaled(
            inner, inner,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        white = _tint(icon, QColor("#FFFFFF"))
        p.drawPixmap((size - white.width()) // 2, (size - white.height()) // 2, white)

    p.end()
    return badge


def _tint(src: QPixmap, color: QColor) -> QPixmap:
    result = QPixmap(src.size())
    result.fill(Qt.GlobalColor.transparent)
    p = QPainter(result)
    p.drawPixmap(0, 0, src)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    p.fillRect(result.rect(), color)
    p.end()
    return result


def _fallback_icon(color: QColor, size: int) -> QPixmap:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(0, 0, size, size)
    p.end()
    return px
