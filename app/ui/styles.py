from app.config.config_loader import ConfigLoader

# Design token defaults — "Чистая точность" variant
_LIGHT = {
    "background":     "#eef1f5",
    "surface":        "#ffffff",
    "menu_background":"#ffffff",
    "text_primary":   "#192230",
    "text_secondary": "#5d6b7e",
    "primary":        "#1f6feb",
    "on_primary":     "#ffffff",
    "border":         "#e1e6ee",
    "error_critical": "#d92d20",
    "error_warning":  "#e8830c",
}
_DARK = {
    "background":     "#1b2634",
    "surface":        "#27323f",
    "menu_background":"#202b3a",
    "text_primary":   "#f1f5fa",
    "text_secondary": "#a4b2c4",
    "primary":        "#5b9bff",
    "on_primary":     "#0a1018",
    "border":         "#3a4655",
    "error_critical": "#ff6157",
    "error_warning":  "#ffb13b",
}


def _rgba(hex_color: str, alpha: int) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def get_tokens(config: ConfigLoader, theme: str) -> dict:
    """Return merged color tokens for the given theme."""
    defaults = _DARK if theme == "dark" else _LIGHT
    key = "colors_dark" if theme == "dark" else "colors_light"
    return {**defaults, **config.ui.get(key, {})}


def build_stylesheet(config: ConfigLoader, theme: str = "light") -> str:
    c = get_tokens(config, theme)

    bg      = c["background"]
    surface = c["surface"]
    fg      = c["text_primary"]
    fg2     = c["text_secondary"]
    primary = c["primary"]
    border  = c["border"]
    menu_bg = c["menu_background"]
    crit    = c["error_critical"]
    warn    = c["error_warning"]
    on_pri  = c.get("on_primary", "#ffffff")

    primary_dim  = _rgba(primary, 30)
    primary_mid  = _rgba(primary, 50)
    danger_hover = "#b92319" if theme == "light" else "#ff7a72"

    return f"""
/* ── Base ──────────────────────────────────────────────────────── */
QMainWindow, QWidget {{
    background-color: {bg};
    color: {fg};
    font-family: "IBM Plex Sans", "Segoe UI", "Ubuntu", sans-serif;
    font-size: 14px;
}}

/* ── Top bar ────────────────────────────────────────────────────── */
QWidget#topBar {{
    background-color: {menu_bg};
    border-bottom: 1px solid {border};
}}

/* ── Time label ─────────────────────────────────────────────────── */
QLabel#labelTime {{
    font-family: "IBM Plex Mono", "Courier New", monospace;
    font-size: 30px;
    font-weight: 700;
    color: {fg};
    letter-spacing: 1px;
    background: transparent;
}}

/* ── Crop label ─────────────────────────────────────────────────── */
QLabel#labelCropCaption {{
    font-size: 10px;
    font-weight: 600;
    color: {fg2};
    letter-spacing: 2px;
    text-transform: uppercase;
    background: transparent;
}}
QLabel#labelCropName {{
    font-size: 18px;
    font-weight: 600;
    color: {fg};
    background: transparent;
}}

/* ── МЕНЮ pill button ───────────────────────────────────────────── */
QPushButton#btnMenu {{
    background-color: {primary};
    color: {on_pri};
    border: none;
    border-radius: 21px;
    font-size: 17px;
    font-weight: 700;
    padding: 0 20px;
}}
QPushButton#btnMenu:pressed {{ background-color: {_rgba(primary, 210)}; }}

/* ── Panel dividers ─────────────────────────────────────────────── */
QFrame#divider {{
    background-color: {border};
    border: none;
}}

/* ── Sensor column background ───────────────────────────────────── */
QWidget#sensorColumn {{
    background-color: {bg};
}}

/* ── Sensor card ────────────────────────────────────────────────── */
QFrame#sensorCard {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 16px;
}}
QFrame#sensorCard[state="warning"] {{
    border: 2px solid {warn};
}}
QFrame#sensorCard[state="critical"] {{
    border: 2px solid {crit};
}}
QLabel#cardName {{
    font-size: 12px;
    font-weight: 600;
    color: {fg2};
    background: transparent;
}}
QLabel#cardValue {{
    font-family: "IBM Plex Mono", "Courier New", monospace;
    font-size: 31px;
    font-weight: 700;
    color: {fg};
    background: transparent;
}}
QLabel#cardValueWarn {{
    font-family: "IBM Plex Mono", "Courier New", monospace;
    font-size: 31px;
    font-weight: 700;
    color: {warn};
    background: transparent;
}}
QLabel#cardValueCrit {{
    font-family: "IBM Plex Mono", "Courier New", monospace;
    font-size: 31px;
    font-weight: 700;
    color: {crit};
    background: transparent;
}}
QLabel#cardUnit {{
    font-size: 12px;
    font-weight: 500;
    color: {fg2};
    background: transparent;
}}

/* ── Center panel ───────────────────────────────────────────────── */
QWidget#panelCenter {{
    background-color: {bg};
}}

/* ── Fault icon buttons ─────────────────────────────────────────── */
QPushButton#faultBtn {{
    background-color: transparent;
    border: none;
}}

/* ── Dialog / full-screen menu ──────────────────────────────────── */
QDialog {{
    background-color: {bg};
    color: {fg};
    border: none;
}}
QWidget#menuHeader {{
    background-color: {menu_bg};
    border-bottom: 1px solid {border};
}}
QLabel#menuTitle {{
    font-size: 22px;
    font-weight: 600;
    color: {fg};
    background: transparent;
}}

/* ── Menu nav card ──────────────────────────────────────────────── */
QPushButton#menuNavCard {{
    background-color: {surface};
    color: {fg};
    border: 1px solid {border};
    border-radius: 16px;
    font-size: 19px;
    font-weight: 600;
    text-align: left;
    padding: 0 18px;
}}
QPushButton#menuNavCard:pressed {{ background-color: {_rgba(primary, 20)}; }}
QPushButton#menuNavCard[danger="true"] {{
    border: 2px solid {crit};
    color: {crit};
}}

/* ── Icon-back / close buttons ─────────────────────────────────── */
QPushButton#menuIconBtn {{
    background-color: transparent;
    color: {fg};
    border: 1px solid {border};
    border-radius: 10px;
}}
QPushButton#menuIconBtn:pressed {{ background-color: {_rgba(primary, 30)}; }}

/* ── Crop list row ──────────────────────────────────────────────── */
QPushButton#cropRow {{
    background-color: transparent;
    color: {fg};
    border: none;
    border-top: 1px solid {border};
    font-size: 18px;
    font-weight: 500;
    text-align: left;
    padding: 0 18px;
}}
QPushButton#cropRow:pressed {{ background-color: {_rgba(primary, 20)}; }}
QPushButton#cropRow[selected="true"] {{
    color: {primary};
    font-weight: 600;
}}

/* ── Section label ──────────────────────────────────────────────── */
QLabel#sectionLabel {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    color: {fg2};
    background: transparent;
}}

/* ── Card container (crop list, sensor list, etc.) ──────────────── */
QFrame#listCard {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 16px;
}}

/* ── Sensor toggle row ──────────────────────────────────────────── */
QLabel#sensorRowLabel {{
    font-size: 16px;
    font-weight: 500;
    color: {fg};
    background: transparent;
}}

/* ── Segmented toggle buttons ───────────────────────────────────── */
QPushButton#segBtn {{
    background-color: transparent;
    color: {fg2};
    border: none;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 600;
}}
QPushButton#segBtn:checked {{
    background-color: {primary};
    color: {on_pri};
}}
QPushButton#segBtn:pressed:!checked {{ background-color: {_rgba(primary, 20)}; }}

/* ── Statistics period buttons ──────────────────────────────────── */
QPushButton#periodBtn {{
    background-color: transparent;
    color: {fg2};
    border: none;
    border-radius: 11px;
    font-size: 16px;
    font-weight: 600;
}}
QPushButton#periodBtn:checked {{
    background-color: {primary};
    color: {on_pri};
}}

/* ── Export button ──────────────────────────────────────────────── */
QPushButton#exportBtn {{
    background-color: #22a05a;
    color: #ffffff;
    border: none;
    border-radius: 999px;
    font-size: 16px;
    font-weight: 700;
    padding: 0 22px;
}}
QPushButton#exportSaved {{
    background-color: transparent;
    color: #22a05a;
    border: 1px solid {border};
    border-radius: 999px;
    font-size: 16px;
    font-weight: 700;
    padding: 0 22px;
}}

/* ── Stats metric card ──────────────────────────────────────────── */
QFrame#metricCard {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 16px;
}}
QLabel#metricValue {{
    font-family: "IBM Plex Mono", "Courier New", monospace;
    font-size: 44px;
    font-weight: 600;
    background: transparent;
}}
QLabel#metricUnit {{
    font-size: 15px;
    font-weight: 600;
    color: {fg2};
    background: transparent;
}}
QLabel#metricLabel {{
    font-size: 13px;
    color: {fg2};
    background: transparent;
    margin-top: 6px;
}}

/* ── Stats detail row ───────────────────────────────────────────── */
QLabel#detailKey {{
    font-size: 16px;
    color: {fg2};
    background: transparent;
}}
QLabel#detailVal {{
    font-family: "IBM Plex Mono", "Courier New", monospace;
    font-size: 16px;
    font-weight: 600;
    color: {fg};
    background: transparent;
}}

/* ── Danger button (shutdown) ───────────────────────────────────── */
QPushButton#dangerBtn {{
    background-color: {crit};
    color: #ffffff;
    border: none;
    border-radius: 999px;
    font-size: 17px;
    font-weight: 700;
    padding: 0 30px;
}}
QPushButton#dangerBtn:pressed {{ background-color: {danger_hover}; }}
QPushButton#cancelBtn {{
    background-color: transparent;
    color: {fg};
    border: 1px solid {border};
    border-radius: 999px;
    font-size: 17px;
    font-weight: 600;
    padding: 0 30px;
}}
QPushButton#cancelBtn:pressed {{ background-color: {_rgba(primary, 20)}; }}

/* ── Scrollbar ──────────────────────────────────────────────────── */
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{
    background: {_rgba(border, 80)};
    width: 14px;
    margin: 2px;
    border-radius: 7px;
}}
QScrollBar::handle:vertical {{
    background: {fg2};
    border-radius: 5px;
    min-height: 40px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{ background: {primary}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

/* ── Error popup dialog ─────────────────────────────────────────── */
QDialog#errorPopup {{
    background-color: #1c1e24;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
}}
QLabel#errTitle {{
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    background: transparent;
}}
QLabel#errDesc {{
    font-size: 15px;
    color: #aab0bd;
    background: transparent;
}}
QPushButton#errClose {{
    background-color: rgba(255,255,255,0.08);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    font-size: 20px;
}}
QPushButton#errClose:pressed {{ background-color: rgba(255,255,255,0.15); }}
"""
