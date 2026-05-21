"""
QtAwesome-based icon helpers with graceful fallback.

If qtawesome is unavailable (e.g. fresh install without pip deps), returns
empty QIcon — the program keeps working, just without icons next to text.
"""
from PyQt6.QtGui import QIcon

try:
    import qtawesome as qta
    _HAS_QTA = True
except Exception:
    _HAS_QTA = False


# Material Design Icons (mdi) names → semantic keys used across the app
ICON_MAP = {
    "settings":   "mdi.cog",
    "stats":      "mdi.chart-line",
    "errors":     "mdi.alert-circle-outline",
    "shutdown":   "mdi.power",
    "back":       "mdi.arrow-left",
    "theme_light": "mdi.white-balance-sunny",
    "theme_dark":  "mdi.weather-night",
    "opaque":     "mdi.square",
    "transparent": "mdi.square-outline",
    "windowed":   "mdi.window-restore",
    "fullscreen": "mdi.fullscreen",
    "close":      "mdi.close",
}


def icon(key: str, color: str = "#1A1A1A") -> QIcon:
    """Return QIcon for a semantic key. Falls back to empty QIcon if qtawesome missing."""
    if not _HAS_QTA:
        return QIcon()
    mdi_name = ICON_MAP.get(key)
    if not mdi_name:
        return QIcon()
    try:
        return qta.icon(mdi_name, color=color)
    except Exception:
        return QIcon()


def has_qtawesome() -> bool:
    return _HAS_QTA
