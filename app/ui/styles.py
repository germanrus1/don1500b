from app.config.config_loader import ConfigLoader


def build_stylesheet(config: ConfigLoader, theme: str = "light") -> str:
    key = "colors_dark" if theme == "dark" else "colors_light"
    c = config.ui.get(key, {})
    f = config.ui.get("fonts", {})

    bg = c.get("background", "#FFFFFF")
    fg = c.get("text_primary", "#000000")
    fg2 = c.get("text_secondary", "#666666")
    border = c.get("border", "#CCCCCC")
    menu_bg = c.get("menu_background", "#F5F5F5")
    err_red = c.get("error_critical", "#E63946")
    err_orange = c.get("error_warning", "#F77F00")

    f_value = f.get("value", 28)
    f_label = f.get("label", 16)
    f_time = f.get("time", 24)
    f_menu = f.get("menu", 18)

    desc_bg = "#2D2D2D" if theme == "light" else "#404040"
    desc_fg = "#FFFFFF"

    stylesheet = f"""
QMainWindow, QWidget {{
    background-color: {bg};
    color: {fg};
    font-family: "Ubuntu", "Segoe UI", "Arial", sans-serif;
}}
QWidget#topBar {{
    background-color: {menu_bg};
    border-bottom: 1px solid {border};
}}
QLabel {{
    background: transparent;
    color: {fg};
}}
QLabel#labelTime {{
    font-size: {f_time}px;
    font-weight: bold;
}}
QLabel#labelCulture {{
    font-size: {f_label}px;
    color: {fg2};
}}
QPushButton#btnMenu {{
    background-color: {bg};
    color: {fg};
    border: 2px solid {border};
    border-radius: 6px;
    font-size: {f_menu}px;
    font-weight: bold;
    padding: 4px 12px;
}}
QPushButton#btnMenu:hover {{
    background-color: {border};
}}
QPushButton#btnMenu:pressed {{
    background-color: {menu_bg};
}}
QFrame#panelRight {{
    background-color: {menu_bg};
    border-left: 1px solid {border};
}}
QLabel#sensorLabel {{
    font-size: {f_label}px;
    color: {fg2};
}}
QLabel#sensorValue {{
    font-size: {f_value}px;
    font-weight: bold;
    color: {fg};
}}
QWidget#sensorSep {{
    background-color: {border};
}}
QFrame#errorDescBox {{
    background-color: {desc_bg};
    border-radius: 8px;
    border: 1px solid #1A1A1A;
}}
QLabel#errorDescTitle {{
    font-size: 17px;
    font-weight: bold;
    color: {desc_fg};
    background: transparent;
}}
QLabel#errorDescText {{
    font-size: 14px;
    color: {desc_fg};
    background: transparent;
    line-height: 1.4;
}}
QPushButton#errorDescClose {{
    background: transparent;
    color: {desc_fg};
    border: none;
    font-size: 16px;
    font-weight: bold;
}}
QPushButton#errorDescClose:hover {{
    color: #FF6B6B;
}}

/* ── Menu dialog ───────────────────────────────────────── */
QPushButton#menuNavBtn {{
    background-color: {bg};
    color: {fg};
    border: 2px solid {border};
    border-radius: 8px;
    font-size: 17px;
}}
QPushButton#menuNavBtn:hover {{
    background-color: {menu_bg};
}}
QPushButton#menuCloseBtn {{
    background-color: {menu_bg};
    color: {fg2};
    border: 1px solid {border};
    border-radius: 6px;
    font-size: 15px;
}}
QPushButton#menuBackBtn {{
    background-color: transparent;
    color: {fg};
    border: none;
    font-size: 20px;
    font-weight: bold;
}}
QPushButton#menuBackBtn:hover {{
    color: {err_orange};
}}
QWidget#menuHeader {{
    background-color: {menu_bg};
    border-bottom: 1px solid {border};
}}
QLabel#menuPageTitle {{
    font-size: 18px;
    font-weight: bold;
    color: {fg};
    background: transparent;
}}
QLabel#menuSectionLabel {{
    font-size: 14px;
    color: {fg2};
    background: transparent;
}}
QLabel#menuStatValue {{
    font-size: 20px;
    font-weight: bold;
    color: {fg};
    background: transparent;
}}
QLabel#menuTableHeader {{
    font-size: 13px;
    font-weight: bold;
    color: {fg2};
    background: transparent;
}}
QLabel#menuTableRow {{
    font-size: 13px;
    color: {fg};
    background: transparent;
}}
QPushButton#menuToggleBtn {{
    background-color: {bg};
    color: {fg};
    border: 2px solid {border};
    border-radius: 6px;
    font-size: 15px;
    padding: 4px 8px;
}}
QPushButton#menuToggleBtn:checked {{
    background-color: #2E86AB;
    color: #FFFFFF;
    border-color: #1A6A8A;
}}
QPushButton#menuToggleBtn:hover:!checked {{
    background-color: {menu_bg};
}}
QPushButton#menuDangerBtn {{
    background-color: {err_red};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-size: 17px;
    font-weight: bold;
}}
QPushButton#menuDangerBtn:hover {{
    background-color: #C0303A;
}}
QFrame#menuSep {{
    border: none;
    border-bottom: 1px solid {border};
    background: transparent;
}}
"""

    if config.ui.get("transparent", False):
        stylesheet += f"""
QMainWindow {{ background: transparent; }}
QWidget {{ background: transparent; }}
QFrame#panelCenter {{ background: transparent; }}
QFrame#panelRight {{ background: transparent; border: none; }}
QWidget#topBar {{ background-color: {menu_bg}; border-bottom: 1px solid {border}; }}
"""

    return stylesheet
