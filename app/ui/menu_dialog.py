from datetime import datetime
from typing import List, Optional

from PyQt6.QtCore import QPoint, QPointF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QBrush, QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QScroller,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.config_loader import ConfigLoader
from app.logger.data_logger import DataLogger
from app.ui.styles import build_stylesheet, get_tokens

try:
    import qtawesome as qta
    _HAS_QTA = True
except Exception:
    _HAS_QTA = False


_DEFAULT_CULTURES = ["Пшеница", "Ячмень", "Рожь", "Овёс", "Кукуруза", "Подсолнечник"]

_SENSOR_DISPLAY = [
    {"id": "erpm",  "label": "Обороты двигателя",                "mdi": "mdi.cog",              "color": "#7c5cf0"},
    {"id": "etemp", "label": "Температура охлаждающей жидкости", "mdi": "mdi.thermometer",       "color": "#e85d3a"},
    {"id": "oil",   "label": "Давление масла в двигателе",       "mdi": "mdi.gauge",             "color": "#5b6ef0"},
    {"id": "fuel",  "label": "Уровень топлива в баке",           "mdi": "mdi.gas-station",       "color": "#f0871a"},
    {"id": "volt",  "label": "Напряжение бортовой сети",         "mdi": "mdi.lightning-bolt",    "color": "#e0930f"},
    {"id": "drum",  "label": "Частота молотильного барабана",    "mdi": "mdi.rotate-3d-variant", "color": "#3b82f6"},
    {"id": "auger", "label": "Обороты колосового шнека",         "mdi": "mdi.swap-horizontal",   "color": "#22a05a"},
    {"id": "fan",   "label": "Вентилятор системы очистки",       "mdi": "mdi.fan",               "color": "#0ea5b5"},
    {"id": "moist", "label": "Влажность зерна",                  "mdi": "mdi.water",             "color": "#14a08a"},
    {"id": "loss",  "label": "Потери зерна за молотилкой",       "mdi": "mdi.grain",             "color": "#d6479b"},
]

_PAGE_ROOT    = 0
_PAGE_CROP    = 1
_PAGE_SENSORS = 2
_PAGE_THEME   = 3
_PAGE_STATS   = 4
_PAGE_POWER   = 5

_TITLES = {
    _PAGE_ROOT:    "Меню",
    _PAGE_CROP:    "Культура",
    _PAGE_SENSORS: "Датчики",
    _PAGE_THEME:   "Тема",
    _PAGE_STATS:   "Статистика",
    _PAGE_POWER:   "Выключение",
}


# ── Toggle switch widget ───────────────────────────────────────────────────

class _Toggle(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, on_color: str = "#1f6feb",
                 off_color: str = "#e1e6ee", parent=None):
        super().__init__(parent)
        self._checked   = checked
        self._on_color  = QColor(on_color)
        self._off_color = QColor(off_color)
        self.setFixedSize(54, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def is_checked(self) -> bool:
        return self._checked

    def set_colors(self, on_color: str, off_color: str):
        self._on_color  = QColor(on_color)
        self._off_color = QColor(off_color)
        self.update()

    def mousePressEvent(self, _e):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r    = h / 2

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._on_color if self._checked else self._off_color))
        p.drawRoundedRect(0, 0, w, h, r, r)

        d  = 26
        mg = (h - d) / 2
        cx = w - mg - d / 2 if self._checked else mg + d / 2
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QPointF(cx, h / 2), d / 2, d / 2)
        p.end()


# ── Nav card ───────────────────────────────────────────────────────────────

def _nav_card_pixmap(mdi: str, color_hex: str, is_dark: bool,
                     chip: int = 50, radius: int = 12) -> QPixmap:
    alpha = int(255 * (0.24 if is_dark else 0.16))
    c     = QColor(color_hex)
    bg    = QColor(c.red(), c.green(), c.blue(), alpha)

    px = QPixmap(chip, chip)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(bg))
    p.drawRoundedRect(0, 0, chip, chip, radius, radius)
    if _HAS_QTA:
        try:
            icon_px = qta.icon(mdi, color=color_hex).pixmap(30, 30)
            off = (chip - 30) // 2
            p.drawPixmap(off, off, icon_px)
        except Exception:
            pass
    p.end()
    return px


class _NavCard(QWidget):
    clicked = pyqtSignal()

    def __init__(self, mdi: str, label: str, color: str, is_dark: bool,
                 danger: bool = False, tokens: dict = None, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._danger = danger

        frame = QFrame(self)
        frame.setObjectName("menuNavCard")
        if danger:
            frame.setProperty("danger", "true")
            frame.setStyleSheet("QFrame#menuNavCard { border: 2px solid "
                                + (tokens or {}).get("error_critical", "#d92d20") + "; border-radius: 16px; }")
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        vl = QVBoxLayout(frame)
        vl.setContentsMargins(18, 20, 18, 18)
        vl.setSpacing(0)
        vl.setAlignment(Qt.AlignmentFlag.AlignLeft)

        chip_lbl = QLabel()
        chip_lbl.setFixedSize(50, 50)
        chip_lbl.setPixmap(_nav_card_pixmap(mdi, color, is_dark))
        chip_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        vl.addWidget(chip_lbl)

        vl.addStretch()

        fg  = (tokens or {}).get("error_critical" if danger else "text_primary", "#192230")
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"font-size: 19px; font-weight: 600; color: {fg}; background: transparent;"
        )
        vl.addWidget(lbl)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

    def mousePressEvent(self, _e):
        self.clicked.emit()

    def mouseReleaseEvent(self, _e):
        pass


# ── Section label helper ───────────────────────────────────────────────────

def _sec_lbl(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("sectionLabel")
    return lbl


# ── Menu dialog ────────────────────────────────────────────────────────────

class MenuDialog(QDialog):
    theme_changed       = pyqtSignal(str)
    culture_changed     = pyqtSignal(str)
    window_mode_changed = pyqtSignal(str)
    transparent_changed = pyqtSignal(bool)
    sensors_changed     = pyqtSignal()

    def __init__(self, config: ConfigLoader, stats: dict, logger: DataLogger,
                 collector=None, current_theme: str = "light", parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self._config    = config
        self._stats     = stats
        self._logger    = logger
        self._collector = collector
        self._theme     = current_theme
        self._tokens    = get_tokens(config, current_theme)
        self._is_dark   = current_theme == "dark"

        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        if parent is not None:
            self.setFixedSize(parent.size())
            self.move(parent.mapToGlobal(QPoint(0, 0)))
        else:
            self.setFixedSize(1024, 600)

        self._build_ui()
        self.setStyleSheet(build_stylesheet(config, current_theme))

    # ── Build skeleton ─────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setObjectName("menuHeader")
        hdr.setFixedHeight(62)
        hdr_hl = QHBoxLayout(hdr)
        hdr_hl.setContentsMargins(16, 0, 16, 0)
        hdr_hl.setSpacing(12)

        self._back_btn = QPushButton()
        self._back_btn.setObjectName("menuIconBtn")
        self._back_btn.setFixedSize(44, 44)
        self._back_btn.clicked.connect(self._go_root)
        self._back_btn.hide()
        self._set_icon(self._back_btn, "mdi.arrow-left")
        hdr_hl.addWidget(self._back_btn)

        self._title_lbl = QLabel("Меню")
        self._title_lbl.setObjectName("menuTitle")
        hdr_hl.addWidget(self._title_lbl, stretch=1)

        close_btn = QPushButton()
        close_btn.setObjectName("menuIconBtn")
        close_btn.setFixedSize(44, 44)
        close_btn.clicked.connect(self.accept)
        self._set_icon(close_btn, "mdi.close")
        hdr_hl.addWidget(close_btn)
        root.addWidget(hdr)

        # ── Stacked pages ─────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_root())
        self._stack.addWidget(self._page_crop())
        self._stack.addWidget(self._page_sensors())
        self._stack.addWidget(self._page_theme())
        self._stack.addWidget(self._page_stats())
        self._stack.addWidget(self._page_power())
        root.addWidget(self._stack, stretch=1)

    def _goto(self, idx: int):
        if idx == _PAGE_STATS:
            # Rebuild stats page fresh each time so data is current
            old = self._stack.widget(_PAGE_STATS)
            new = self._page_stats()
            self._stack.removeWidget(old)
            old.deleteLater()
            self._stack.insertWidget(_PAGE_STATS, new)
        self._stack.setCurrentIndex(idx)
        self._title_lbl.setText(_TITLES.get(idx, ""))
        self._back_btn.setVisible(idx != _PAGE_ROOT)

    def _go_root(self):
        self._goto(_PAGE_ROOT)

    def _set_icon(self, btn: QPushButton, mdi_name: str):
        if _HAS_QTA:
            try:
                btn.setIcon(qta.icon(mdi_name, color=self._tokens.get("text_primary", "#192230")))
            except Exception:
                pass

    def _icon_color(self) -> str:
        return self._tokens.get("text_primary", "#192230")

    # ── Page 0: root ───────────────────────────────────────────────────────

    def _page_root(self) -> QWidget:
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        body = QWidget()
        bl   = QVBoxLayout(body)
        bl.setContentsMargins(22, 20, 22, 28)
        bl.setSpacing(14)

        bl.addWidget(_sec_lbl("Навигация"))

        nav_items = [
            ("mdi.leaf",              "Культура",  "#22a05a", _PAGE_CROP,    False),
            ("mdi.radar",             "Датчики",   "#3b82f6", _PAGE_SENSORS, False),
            ("mdi.contrast",          "Тема",      "#7c5cf0", _PAGE_THEME,   False),
            ("mdi.chart-bar",         "Статистика","#f0871a", _PAGE_STATS,   False),
            ("mdi.power-settings-new","Выключить", "#d92d20", _PAGE_POWER,   True),
        ]

        grid = QGridLayout()
        grid.setSpacing(14)
        for i, (mdi, label, color, page_idx, danger) in enumerate(nav_items):
            card = _NavCard(mdi, label, color, self._is_dark, danger, self._tokens)
            card.setFixedHeight(124)
            card.clicked.connect(lambda idx=page_idx: self._goto(idx))
            grid.addWidget(card, i // 3, i % 3)

        bl.addLayout(grid)
        bl.addStretch()

        scroll.setWidget(body)
        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
        return page

    # ── Page 1: crop ───────────────────────────────────────────────────────

    def _page_crop(self) -> QWidget:
        page   = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        body = QWidget()
        bl   = QVBoxLayout(body)
        bl.setContentsMargins(22, 20, 22, 28)
        bl.setSpacing(12)
        bl.addWidget(_sec_lbl("Выбор культуры"))

        card = QFrame()
        card.setObjectName("listCard")
        cvl  = QVBoxLayout(card)
        cvl.setContentsMargins(0, 0, 0, 0)
        cvl.setSpacing(0)

        cultures = self._config.interface.get("cultures", _DEFAULT_CULTURES)

        # Store button refs so we can update checkmarks in-place
        self._crop_btns: dict = {}

        for i, name in enumerate(cultures):
            btn = QPushButton(name)
            btn.setObjectName("cropRow")
            btn.setFixedHeight(60)
            if i == 0:
                btn.setStyleSheet("QPushButton#cropRow { border-top: none; }")
            self._crop_btns[name] = btn
            btn.clicked.connect(lambda _, n=name: self._on_crop(n))
            cvl.addWidget(btn)

        # Apply initial checkmark
        self._apply_crop_checkmarks()

        bl.addWidget(card)
        bl.addStretch()
        scroll.setWidget(body)

        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
        return page

    def _apply_crop_checkmarks(self):
        current = self._stats.get("culture", "")
        primary = self._tokens.get("primary", "#1f6feb")
        fg      = self._tokens.get("text_primary", "#192230")
        check_icon = qta.icon("mdi.check-circle", color=primary) if _HAS_QTA else QIcon()

        for name, btn in self._crop_btns.items():
            selected = name.lower() == current.lower()
            if selected:
                btn.setIcon(check_icon)
                btn.setIconSize(QSize(22, 22))
                btn.setStyleSheet(
                    f"QPushButton#cropRow {{ color: {primary}; font-weight: 600; "
                    f"border-top: 1px solid {self._tokens.get('border','#e1e6ee')}; }}"
                )
            else:
                btn.setIcon(QIcon())
                btn.setStyleSheet("")

    def _on_crop(self, name: str):
        self._stats["culture"] = name
        self.culture_changed.emit(name)
        # Update checkmarks in-place without leaving the page
        self._apply_crop_checkmarks()

    # ── Page 2: sensors ────────────────────────────────────────────────────

    def _page_sensors(self) -> QWidget:
        page   = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        body = QWidget()
        bl   = QVBoxLayout(body)
        bl.setContentsMargins(22, 20, 22, 28)
        bl.setSpacing(12)
        bl.addWidget(_sec_lbl("Активные датчики"))

        list_card = QFrame()
        list_card.setObjectName("listCard")
        lcl = QVBoxLayout(list_card)
        lcl.setContentsMargins(0, 0, 0, 0)
        lcl.setSpacing(0)

        off_color  = self._tokens.get("border", "#e1e6ee")
        sensors_cfg = self._config.sensors.get("list", {})

        for i, s in enumerate(_SENSOR_DISPLAY):
            cfg_id  = s["id"]
            enabled = sensors_cfg.get(cfg_id, {}).get("enabled", True)

            row = QWidget()
            rl  = QHBoxLayout(row)
            rl.setContentsMargins(16, 0, 16, 0)
            rl.setSpacing(13)
            row.setFixedHeight(60)
            if i > 0:
                row.setStyleSheet(
                    f"border-top: 1px solid {off_color};"
                )

            chip = QLabel()
            chip.setFixedSize(38, 38)
            chip.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            chip.setPixmap(self._small_chip(s["mdi"], s["color"]))
            rl.addWidget(chip)

            name_lbl = QLabel(s["label"])
            name_lbl.setObjectName("sensorRowLabel")
            name_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            rl.addWidget(name_lbl, stretch=1)

            toggle = _Toggle(checked=enabled, on_color=s["color"], off_color=off_color)
            toggle.toggled.connect(
                lambda val, sid=cfg_id: self._on_sensor_toggle(sid, val)
            )
            rl.addWidget(toggle)

            lcl.addWidget(row)

        bl.addWidget(list_card)
        bl.addSpacing(8)
        bl.addWidget(_sec_lbl("Диагностика"))

        diag_card = QFrame()
        diag_card.setObjectName("listCard")
        diag_card.setFixedHeight(62)
        dl = QHBoxLayout(diag_card)
        dl.setContentsMargins(18, 0, 18, 0)
        dl.setSpacing(0)

        diag_info = QWidget()
        dil = QVBoxLayout(diag_info)
        dil.setContentsMargins(0, 0, 0, 0)
        dil.setSpacing(2)
        title_lbl = QLabel("Имитация неисправностей")
        title_lbl.setObjectName("sensorRowLabel")
        dil.addWidget(title_lbl)
        sub_lbl = QLabel("Демонстрация экрана с ошибками")
        sub_lbl.setObjectName("sectionLabel")
        dil.addWidget(sub_lbl)
        dl.addWidget(diag_info, stretch=1)

        warn_color = self._tokens.get("error_warning", "#e8830c")
        sim_toggle = _Toggle(checked=False, on_color=warn_color, off_color=off_color)
        dl.addWidget(sim_toggle)
        bl.addWidget(diag_card)
        bl.addStretch()

        scroll.setWidget(body)
        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
        return page

    def _small_chip(self, mdi: str, color_hex: str) -> QPixmap:
        sz = 38
        r  = 10
        c  = QColor(color_hex)
        alpha = int(255 * (0.22 if self._is_dark else 0.15))
        bg = QColor(c.red(), c.green(), c.blue(), alpha)
        px = QPixmap(sz, sz)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(0, 0, sz, sz, r, r)
        if _HAS_QTA:
            try:
                icon_px = qta.icon(mdi, color=color_hex).pixmap(22, 22)
                p.drawPixmap((sz - 22) // 2, (sz - 22) // 2, icon_px)
            except Exception:
                pass
        p.end()
        return px

    def _on_sensor_toggle(self, sensor_id: str, enabled: bool):
        self._config.set_and_save(f"sensors.list.{sensor_id}.enabled", enabled)
        self.sensors_changed.emit()

    # ── Page 3: theme ──────────────────────────────────────────────────────

    def _page_theme(self) -> QWidget:
        page = QWidget()
        pl   = QVBoxLayout(page)
        pl.setContentsMargins(22, 20, 22, 28)
        pl.setSpacing(16)
        pl.setAlignment(Qt.AlignmentFlag.AlignTop)

        pl.addWidget(_sec_lbl("Оформление дисплея"))

        seg_frame = QFrame()
        seg_frame.setObjectName("listCard")
        seg_frame.setFixedHeight(68)
        seg_hl = QHBoxLayout(seg_frame)
        seg_hl.setContentsMargins(6, 6, 6, 6)
        seg_hl.setSpacing(0)

        btn_group = QButtonGroup(self)
        btn_group.setExclusive(True)

        for val, label, mdi in [("light", "Светлая", "mdi.white-balance-sunny"),
                                  ("dark",  "Тёмная",  "mdi.weather-night")]:
            btn = QPushButton(f"  {label}")
            btn.setObjectName("segBtn")
            btn.setCheckable(True)
            btn.setChecked(self._theme == val)
            btn.setFixedHeight(56)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            if _HAS_QTA:
                try:
                    icon_color = self._tokens.get("on_primary", "#ffffff") if self._theme == val \
                                 else self._tokens.get("text_secondary", "#5d6b7e")
                    btn.setIcon(qta.icon(mdi, color=icon_color))
                except Exception:
                    pass
            btn.clicked.connect(lambda _, v=val: self._on_theme(v))
            btn_group.addButton(btn)
            seg_hl.addWidget(btn)

        pl.addWidget(seg_frame)

        # Window mode
        pl.addWidget(_sec_lbl("Режим окна"))

        mode_frame = QFrame()
        mode_frame.setObjectName("listCard")
        mode_frame.setFixedHeight(68)
        mode_hl = QHBoxLayout(mode_frame)
        mode_hl.setContentsMargins(6, 6, 6, 6)
        mode_hl.setSpacing(0)

        mode_group = QButtonGroup(self)
        mode_group.setExclusive(True)
        current_mode = self._config.ui.get("window_mode", "windowed")

        for val, label in [("windowed", "Оконный"), ("fullscreen", "Полный экран")]:
            btn = QPushButton(label)
            btn.setObjectName("segBtn")
            btn.setCheckable(True)
            btn.setChecked(current_mode == val)
            btn.setFixedHeight(56)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _, v=val: self._on_window_mode(v))
            mode_group.addButton(btn)
            mode_hl.addWidget(btn)

        pl.addWidget(mode_frame)
        pl.addStretch()
        return page

    def _on_theme(self, theme: str):
        self._theme   = theme
        self._tokens  = get_tokens(self._config, theme)
        self._is_dark = theme == "dark"
        self.setStyleSheet(build_stylesheet(self._config, theme))
        self.theme_changed.emit(theme)

    def _on_window_mode(self, mode: str):
        self._config.set_and_save("ui.window_mode", mode)
        self.window_mode_changed.emit(mode)

    # ── Page 4: statistics ─────────────────────────────────────────────────

    def _page_stats(self) -> QWidget:
        if self._collector is not None:
            try:
                from app.ui.statistics_screen import StatsPage
                page = StatsPage(self._collector, self._config,
                                 back_fn=self._go_root, parent=self)
                return page
            except Exception:
                pass
        return self._page_stats_simple()

    def _page_stats_simple(self) -> QWidget:
        page   = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        body = QWidget()
        bl   = QVBoxLayout(body)
        bl.setContentsMargins(22, 20, 22, 28)
        bl.setSpacing(16)

        # Period selector + export button
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        period_frame = QFrame()
        period_frame.setObjectName("listCard")
        period_frame.setFixedHeight(58)
        phl = QHBoxLayout(period_frame)
        phl.setContentsMargins(5, 5, 5, 5)
        phl.setSpacing(0)

        period_group = QButtonGroup(self)
        period_group.setExclusive(True)
        self._period = "day"
        self._stat_containers: List[QWidget] = []  # updated on period change

        for val, label in [("day", "За день"), ("week", "За неделю"), ("season", "За сезон")]:
            btn = QPushButton(label)
            btn.setObjectName("periodBtn")
            btn.setCheckable(True)
            btn.setChecked(val == "day")
            btn.setFixedHeight(48)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _, v=val: setattr(self, "_period", v))
            period_group.addButton(btn)
            phl.addWidget(btn)

        top_row.addWidget(period_frame, stretch=1)

        self._export_btn = QPushButton("  Экспорт")
        self._export_btn.setObjectName("exportBtn")
        self._export_btn.setFixedSize(140, 58)
        if _HAS_QTA:
            try:
                self._export_btn.setIcon(qta.icon("mdi.download", color="#ffffff"))
            except Exception:
                pass
        self._export_btn.clicked.connect(self._on_export)
        top_row.addWidget(self._export_btn)
        bl.addLayout(top_row)

        # Summary stats
        stats = self._get_stats()

        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(14)
        for i, (val, unit, label, color) in enumerate([
            (stats.get("area",    "—"), "га",  "Площадь",          "#22a05a"),
            (stats.get("unloads", "—"), "шт",  "Разгрузок бункера","#f0871a"),
            (stats.get("harvest", "—"), "т",   "Намолот",          "#3b82f6"),
        ]):
            mc = QFrame()
            mc.setObjectName("metricCard")
            mc.setStyleSheet(
                f"QFrame#metricCard {{ border-top: 3px solid {color}; "
                f"border-left: 1px solid {self._tokens.get('border','#e1e6ee')}; "
                f"border-right: 1px solid {self._tokens.get('border','#e1e6ee')}; "
                f"border-bottom: 1px solid {self._tokens.get('border','#e1e6ee')}; "
                f"border-radius: 16px; background-color: {self._tokens.get('surface','#ffffff')}; }}"
            )
            mc_vl = QVBoxLayout(mc)
            mc_vl.setContentsMargins(18, 16, 18, 16)
            mc_vl.setSpacing(0)

            val_row = QHBoxLayout()
            val_lbl = QLabel(str(val))
            val_lbl.setObjectName("metricValue")
            val_lbl.setStyleSheet(f"font-family: 'IBM Plex Mono'; font-size: 44px; font-weight: 600; color: {color}; background: transparent;")
            val_row.addWidget(val_lbl)
            u_lbl = QLabel(f" {unit}")
            u_lbl.setObjectName("metricUnit")
            u_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
            val_row.addWidget(u_lbl)
            val_row.addStretch()
            mc_vl.addLayout(val_row)

            cap_lbl = QLabel(label)
            cap_lbl.setObjectName("metricLabel")
            mc_vl.addWidget(cap_lbl)
            metrics_grid.addWidget(mc, 0, i)

        bl.addLayout(metrics_grid)

        # Detail table
        bl.addWidget(_sec_lbl("Детализация"))
        detail_card = QFrame()
        detail_card.setObjectName("listCard")
        dcl = QVBoxLayout(detail_card)
        dcl.setContentsMargins(0, 0, 0, 0)
        dcl.setSpacing(0)

        border  = self._tokens.get("border",     "#e1e6ee")
        surface = self._tokens.get("surface",    "#ffffff")
        bg      = self._tokens.get("background", "#eef1f5")
        rows = self._get_detail_rows(stats)
        for i, (key, val) in enumerate(rows):
            row_w = QWidget()
            rhl   = QHBoxLayout(row_w)
            rhl.setContentsMargins(18, 0, 18, 0)
            row_w.setFixedHeight(54)
            row_bg = bg if i % 2 == 1 else surface
            top_border = f"border-top: 1px solid {border};" if i > 0 else ""
            row_w.setStyleSheet(
                f"background-color: {row_bg}; {top_border}"
            )

            k_lbl = QLabel(key)
            k_lbl.setObjectName("detailKey")
            k_lbl.setStyleSheet("background: transparent;")
            rhl.addWidget(k_lbl, stretch=1)

            v_lbl = QLabel(str(val))
            v_lbl.setObjectName("detailVal")
            v_lbl.setStyleSheet("background: transparent;")
            rhl.addWidget(v_lbl)
            dcl.addWidget(row_w)

        bl.addWidget(detail_card)
        bl.addStretch()

        scroll.setWidget(body)
        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
        return page

    def _get_stats(self) -> dict:
        if self._collector:
            try:
                s = self._collector.get_session_stats()
                return {
                    "area":    f"{s.get('area_ha', 0.0):.1f}",
                    "unloads": str(self._stats.get("unload_count", 0)),
                    "harvest": f"{s.get('harvest_t', 0.0):.1f}",
                    "work_min": s.get("work_min", 0),
                }
            except Exception:
                pass
        elapsed = (datetime.now() - self._stats.get("work_start", datetime.now())).total_seconds() / 60
        return {
            "area":    "—",
            "unloads": str(self._stats.get("unload_count", 0)),
            "harvest": "—",
            "work_min": int(elapsed),
        }

    def _get_detail_rows(self, stats: dict) -> list:
        wm = stats.get("work_min", 0)
        h, m = int(wm // 60), int(wm % 60)
        return [
            ("Дата",          datetime.now().strftime("%d.%m.%Y")),
            ("Время в работе", f"{h} ч {m:02d} мин"),
            ("Культура",       self._stats.get("culture", "—")),
            ("Разгрузок",      str(self._stats.get("unload_count", 0))),
        ]

    def _on_export(self):
        self._export_btn.setText("  Сохранено")
        self._export_btn.setObjectName("exportSaved")
        if _HAS_QTA:
            try:
                self._export_btn.setIcon(qta.icon("mdi.check-circle", color="#22a05a"))
            except Exception:
                pass
        self._export_btn.setStyleSheet("")
        self.setStyleSheet(build_stylesheet(self._config, self._theme))
        QTimer.singleShot(2400, self._reset_export_btn)

    def _reset_export_btn(self):
        self._export_btn.setText("  Экспорт")
        self._export_btn.setObjectName("exportBtn")
        if _HAS_QTA:
            try:
                self._export_btn.setIcon(qta.icon("mdi.download", color="#ffffff"))
            except Exception:
                pass
        self.setStyleSheet(build_stylesheet(self._config, self._theme))

    # ── Page 5: power ──────────────────────────────────────────────────────

    def _page_power(self) -> QWidget:
        page = QWidget()
        vl   = QVBoxLayout(page)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.setSpacing(22)

        # Red icon
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(88, 88)
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setPixmap(self._power_icon_pixmap())
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        vl.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("Выключить компьютер?")
        title.setObjectName("menuTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(title, 0, Qt.AlignmentFlag.AlignHCenter)

        sub = QLabel("Текущая статистика смены будет сохранена.")
        sub.setObjectName("sectionLabel")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(sub, 0, Qt.AlignmentFlag.AlignHCenter)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        cancel = QPushButton("Отмена")
        cancel.setObjectName("cancelBtn")
        cancel.setFixedSize(160, 56)
        cancel.clicked.connect(self._go_root)
        btn_row.addWidget(cancel)

        confirm = QPushButton("  Выключить")
        confirm.setObjectName("dangerBtn")
        confirm.setFixedSize(200, 56)
        if _HAS_QTA:
            try:
                confirm.setIcon(qta.icon("mdi.power", color="#ffffff"))
                confirm.setIconSize(QSize(22, 22))
            except Exception:
                pass
        confirm.clicked.connect(self._do_shutdown)
        btn_row.addWidget(confirm)

        vl.addLayout(btn_row)
        return page

    def _power_icon_pixmap(self) -> QPixmap:
        size  = 88
        color = QColor(self._tokens.get("error_critical", "#d92d20"))
        bg    = QColor(color.red(), color.green(), color.blue(), 31)
        px    = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg))
        p.drawEllipse(0, 0, size, size)
        if _HAS_QTA:
            try:
                icon_px = qta.icon("mdi.power", color=self._tokens.get("error_critical", "#d92d20")).pixmap(48, 48)
                p.drawPixmap((size - 48) // 2, (size - 48) // 2, icon_px)
            except Exception:
                pass
        p.end()
        return px

    def _do_shutdown(self):
        self.accept()
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()
