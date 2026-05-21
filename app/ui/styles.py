from app.config.config_loader import ConfigLoader


def _rgba(hex_color: str, alpha: int) -> str:
    """#RRGGBB + alpha 0-255 → rgba() string for Qt stylesheets."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def build_stylesheet(config: ConfigLoader, theme: str = "light") -> str:
    key = "colors_dark" if theme == "dark" else "colors_light"
    c = config.ui.get(key, {})
    f = config.ui.get("fonts", {})

    bg      = c.get("background",     "#F4F6F8")
    surface = c.get("surface",        "#FFFFFF")
    fg      = c.get("text_primary",   "#1A1A1A")
    fg2     = c.get("text_secondary", "#546E7A")
    primary = c.get("primary",        "#1565C0")
    border  = c.get("border",         "#D1D8E0")
    menu_bg = c.get("menu_background","#E8ECF0")
    err_red = c.get("error_critical", "#C62828")
    err_warn= c.get("error_warning",  "#E65100")

    f_value = f.get("value", 34)
    f_label = f.get("label", 16)
    f_time  = f.get("time",  26)
    f_menu  = f.get("menu",  18)

    # Alpha-blended accent colors for backgrounds/borders
    primary_btn_hover  = _rgba(primary, 22)   # hover bg on transparent elements
    primary_btn_active = _rgba(primary, 38)
    primary_border_dim = _rgba(primary, 80)

    # Danger hover — darker in light, brighter in dark
    danger_hover = "#B71C1C" if theme == "light" else "#EF5350"

    ss = f"""
/* ── Base ──────────────────────────────────────────────────── */
QMainWindow, QWidget {{
    background-color: {bg};
    color: {fg};
    font-family: "Roboto", "Ubuntu", "Segoe UI", sans-serif;
    font-size: 15px;
}}

/* ── Top bar ────────────────────────────────────────────────── */
QWidget#topBar {{
    background-color: {menu_bg};
    border-bottom: 1px solid {border};
}}

/* ── Labels ─────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {fg};
}}
QLabel#labelTime {{
    font-size: {f_time}px;
    font-weight: 700;
    color: {fg};
    letter-spacing: 1px;
}}
QLabel#labelCulture {{
    font-size: {f_label}px;
    color: {fg2};
    font-weight: 500;
}}

/* ── МЕНЮ button — filled pill ──────────────────────────────── */
QPushButton#btnMenu {{
    background-color: {primary};
    color: #FFFFFF;
    border: none;
    border-radius: 21px;
    font-size: {f_label}px;
    font-weight: 700;
    padding: 0 16px;
    letter-spacing: 0.5px;
}}
QPushButton#btnMenu:hover    {{ background-color: {_rgba(primary, 220)}; }}
QPushButton#btnMenu:pressed  {{ background-color: {_rgba(primary, 255)}; }}

/* ── Right panel ─────────────────────────────────────────────── */
QFrame#panelRight {{
    background-color: {bg};
    border-left: 1px solid {border};
}}

/* ── Sensor cards ────────────────────────────────────────────── */
QFrame#sensorCard {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 14px;
}}
QFrame#sensorCard[errorState="warning"] {{
    background-color: {surface};
    border: 2px solid {err_warn};
    border-radius: 14px;
}}
QFrame#sensorCard[errorState="critical"] {{
    background-color: {surface};
    border: 2px solid {err_red};
    border-radius: 14px;
}}
QLabel#sensorCardName {{
    font-size: 13px;
    font-weight: 600;
    color: {fg2};
    background: transparent;
}}
QLabel#sensorValue {{
    font-size: {f_value}px;
    font-weight: 700;
    color: {fg};
    background: transparent;
}}

/* ── Center panel ────────────────────────────────────────────── */
QFrame#panelCenter {{
    background-color: {bg};
}}

/* ── Error description box ───────────────────────────────────── */
QFrame#errorDescBox {{
    background-color: {"#242424" if theme == "light" else "#2E2E2E"};
    border-radius: 12px;
}}
QLabel#errorDescTitle {{
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    background: transparent;
}}
QLabel#errorDescText {{
    font-size: 14px;
    color: #DDDDDD;
    background: transparent;
}}
QPushButton#errorDescClose {{
    background: transparent;
    color: #FFFFFF;
    border: none;
    font-size: 20px;
    font-weight: 700;
}}
QPushButton#errorDescClose:hover {{ color: #EF9A9A; }}

/* ── Dialog — always opaque, visually elevated ───────────────── */
QDialog {{
    background-color: {surface};
    border: 2px solid {border};
    border-radius: 16px;
}}

/* ── Menu header ─────────────────────────────────────────────── */
QWidget#menuHeader {{
    background-color: {menu_bg};
    border-bottom: 1px solid {border};
    border-radius: 0px;
}}
QLabel#menuPageTitle {{
    font-size: 18px;
    font-weight: 700;
    color: {fg};
    background: transparent;
}}

/* ── Back button — bordered, prominent ───────────────────────── */
QPushButton#menuBackBtn {{
    background-color: {primary_btn_hover};
    color: {primary};
    border: 2px solid {primary_border_dim};
    border-radius: 10px;
    font-size: 22px;
    font-weight: 700;
    padding: 0;
}}
QPushButton#menuBackBtn:hover {{
    background-color: {primary_btn_active};
    border-color: {primary};
}}
QPushButton#menuBackBtn:pressed {{
    background-color: {_rgba(primary, 55)};
}}

/* ── Nav buttons — tall, card-like ──────────────────────────── */
QPushButton#menuNavBtn {{
    background-color: {surface};
    color: {fg};
    border: 1px solid {border};
    border-radius: 12px;
    font-size: 17px;
    font-weight: 600;
    text-align: center;
    padding: 0;
}}
QPushButton#menuNavBtn:hover {{
    background-color: {primary_btn_hover};
    border-color: {primary_border_dim};
    color: {primary};
}}
QPushButton#menuNavBtn:pressed {{
    background-color: {primary_btn_active};
}}

/* ── Close button ────────────────────────────────────────────── */
QPushButton#menuCloseBtn {{
    background-color: {menu_bg};
    color: {fg2};
    border: 1px solid {border};
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
}}
QPushButton#menuCloseBtn:hover {{
    background-color: {border};
    color: {fg};
}}

/* ── Section labels ──────────────────────────────────────────── */
QLabel#menuSectionLabel {{
    font-size: 12px;
    font-weight: 700;
    color: {fg2};
    background: transparent;
}}

/* ── Stat values ─────────────────────────────────────────────── */
QLabel#menuStatValue {{
    font-size: 22px;
    font-weight: 700;
    color: {fg};
    background: transparent;
}}
QLabel#menuTableHeader {{
    font-size: 13px;
    font-weight: 700;
    color: {fg2};
    background: transparent;
}}
QLabel#menuTableRow {{
    font-size: 13px;
    color: {fg};
    background: transparent;
}}

/* ── Toggle buttons — segmented look ────────────────────────── */
QPushButton#menuToggleBtn {{
    background-color: {menu_bg};
    color: {fg2};
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    padding: 4px 8px;
}}
QPushButton#menuToggleBtn:checked {{
    background-color: {primary};
    color: #FFFFFF;
}}
QPushButton#menuToggleBtn:hover:!checked {{
    background-color: {border};
    color: {fg};
}}

/* ── Danger button ───────────────────────────────────────────── */
QPushButton#menuDangerBtn {{
    background-color: {err_red};
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 700;
}}
QPushButton#menuDangerBtn:hover  {{ background-color: {danger_hover}; }}
QPushButton#menuDangerBtn:pressed {{ background-color: {danger_hover}; }}

/* ── Sensor settings group ───────────────────────────────────── */
QFrame#sensorSettingsGroup {{
    background-color: {menu_bg};
    border: 1px solid {border};
    border-radius: 10px;
}}

/* ── Separator ───────────────────────────────────────────────── */
QFrame#menuSep {{
    border: none;
    background-color: {border};
}}

/* ── Scrollbar — minimal ─────────────────────────────────────── */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 2px;
    min-height: 32px;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{ background: none; }}
"""

    if config.ui.get("transparent", False):
        ss += f"""
QMainWindow              {{ background-color: transparent; }}
QWidget#centralWidget    {{ background-color: transparent; }}
QFrame#panelCenter       {{ background-color: transparent; }}
QFrame#panelRight        {{ background-color: transparent; border: none; }}
QWidget#topBar           {{ background-color: {_rgba(menu_bg, 220)}; border-bottom: 1px solid {border}; }}
QDialog                  {{ background-color: {surface}; border: 2px solid {border}; border-radius: 16px; }}
"""

    return ss
