from datetime import datetime
from typing import List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.config_loader import ConfigLoader
from app.logger.data_logger import DataLogger
from app.ui.styles import build_stylesheet


_SENSOR_NAMES_RU = {
    "drum":        "Барабан",
    "kolosa":      "Колоса",
    "solomotryas": "Соломотряс",
    "fan_speed":   "Вентилятор",
    "bin_level":   "Бункер",
}
_STATUS_LABELS = {
    "warn_low":  "↓ ниже нормы",
    "warn_high": "↑ выше нормы",
    "critical":  "КРИТИЧ.",
    "ok":        "норма",
}
_DEFAULT_CULTURES = [
    "Пшеница", "Ячмень", "Рапс", "Подсолнечник",
    "Кукуруза", "Горох", "Гречиха", "Овёс",
]

# Indices for QStackedWidget pages
_PAGE_MAIN     = 0
_PAGE_SETTINGS = 1
_PAGE_STATS    = 2
_PAGE_ERRORS   = 3
_PAGE_SHUTDOWN = 4


class MenuDialog(QDialog):
    theme_changed        = pyqtSignal(str)   # "light" | "dark"
    culture_changed      = pyqtSignal(str)   # culture name
    window_mode_changed  = pyqtSignal(str)   # "windowed" | "fullscreen"
    transparent_changed  = pyqtSignal(bool)  # True = transparent

    def __init__(
        self,
        config: ConfigLoader,
        stats: dict,
        logger: DataLogger,
        current_theme: str = "light",
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._stats = stats           # {unload_count, culture, work_start}
        self._logger = logger
        self._theme = current_theme

        self.setWindowTitle("Меню")
        self.setModal(True)
        self.setFixedSize(580, 500)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        self._stack.addWidget(self._page_main())      # 0
        self._stack.addWidget(self._page_settings())  # 1
        self._stack.addWidget(self._page_stats())     # 2
        self._stack.addWidget(self._page_errors())    # 3
        self._stack.addWidget(self._page_shutdown())  # 4

        self.setStyleSheet(build_stylesheet(config, current_theme))

    # ── Navigation ─────────────────────────────────────────────────────────

    def _goto(self, idx: int):
        self._stack.setCurrentIndex(idx)

    def _back_header(self, title: str) -> QWidget:
        header = QWidget()
        header.setObjectName("menuHeader")
        header.setFixedHeight(52)

        row = QHBoxLayout(header)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(8)

        back = QPushButton("←")
        back.setObjectName("menuBackBtn")
        back.setFixedSize(40, 38)
        back.clicked.connect(lambda: self._goto(_PAGE_MAIN))
        row.addWidget(back)

        lbl = QLabel(title)
        lbl.setObjectName("menuPageTitle")
        row.addWidget(lbl)
        row.addStretch()

        return header

    # ── Page 0: main menu ─────────────────────────────────────────────────

    def _page_main(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        for text, idx in [
            ("⚙   Настройки",       _PAGE_SETTINGS),
            ("📊  Статистика",       _PAGE_STATS),
            ("⚠   История ошибок",  _PAGE_ERRORS),
            ("⏻   Выключение",       _PAGE_SHUTDOWN),
        ]:
            btn = QPushButton(text)
            btn.setFixedHeight(58)
            btn.setObjectName("menuNavBtn")
            btn.clicked.connect(lambda _, i=idx: self._goto(i))
            layout.addWidget(btn)

        layout.addStretch()

        close = QPushButton("Закрыть")
        close.setObjectName("menuCloseBtn")
        close.setFixedHeight(44)
        close.clicked.connect(self.accept)
        layout.addWidget(close)

        return page

    # ── Page 1: settings ─────────────────────────────────────────────────

    def _page_settings(self) -> QWidget:
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._back_header("Настройки"))

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 16, 24, 16)
        bl.setSpacing(14)

        # ── Theme ──────────────────────────────────────────────────────────
        bl.addWidget(self._section_label("Тема"))

        theme_row = QHBoxLayout()
        theme_group = QButtonGroup(self)
        theme_group.setExclusive(True)

        btn_light = QPushButton("☀  Светлая")
        btn_light.setCheckable(True)
        btn_light.setChecked(self._theme == "light")
        btn_light.setFixedHeight(44)
        btn_light.setObjectName("menuToggleBtn")
        btn_light.clicked.connect(lambda: self._on_theme("light"))
        theme_group.addButton(btn_light)
        theme_row.addWidget(btn_light)

        btn_dark = QPushButton("🌙  Тёмная")
        btn_dark.setCheckable(True)
        btn_dark.setChecked(self._theme == "dark")
        btn_dark.setFixedHeight(44)
        btn_dark.setObjectName("menuToggleBtn")
        btn_dark.clicked.connect(lambda: self._on_theme("dark"))
        theme_group.addButton(btn_dark)
        theme_row.addWidget(btn_dark)

        bl.addLayout(theme_row)

        # ── Window mode ────────────────────────────────────────────────────
        bl.addWidget(self._section_label("Режим окна"))

        win_row = QHBoxLayout()
        win_group = QButtonGroup(self)
        win_group.setExclusive(True)
        current_mode = self._config.ui.get("window_mode", "windowed")

        btn_win = QPushButton("⊡  Оконный")
        btn_win.setCheckable(True)
        btn_win.setChecked(current_mode == "windowed")
        btn_win.setFixedHeight(44)
        btn_win.setObjectName("menuToggleBtn")
        btn_win.clicked.connect(lambda: self._on_window_mode("windowed"))
        win_group.addButton(btn_win)
        win_row.addWidget(btn_win)

        btn_full = QPushButton("⛶  Полный экран")
        btn_full.setCheckable(True)
        btn_full.setChecked(current_mode == "fullscreen")
        btn_full.setFixedHeight(44)
        btn_full.setObjectName("menuToggleBtn")
        btn_full.clicked.connect(lambda: self._on_window_mode("fullscreen"))
        win_group.addButton(btn_full)
        win_row.addWidget(btn_full)

        bl.addLayout(win_row)

        # ── Culture ────────────────────────────────────────────────────────
        bl.addWidget(self._section_label("Культура"))

        cultures: List[str] = self._config.interface.get("cultures", _DEFAULT_CULTURES)
        current = self._stats.get("culture", "")

        grid = QGridLayout()
        grid.setSpacing(8)
        cult_group = QButtonGroup(self)
        cult_group.setExclusive(True)

        for i, name in enumerate(cultures):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(name.lower() == current.lower())
            btn.setFixedHeight(42)
            btn.setObjectName("menuToggleBtn")
            btn.clicked.connect(lambda _, n=name: self._on_culture(n))
            cult_group.addButton(btn)
            grid.addWidget(btn, i // 2, i % 2)

        bl.addLayout(grid)
        bl.addStretch()
        vbox.addWidget(body)
        return page

    # ── Page 2: statistics ────────────────────────────────────────────────

    def _page_stats(self) -> QWidget:
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._back_header("Статистика"))

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(28, 20, 28, 20)
        bl.setSpacing(0)

        work_start: datetime = self._stats.get("work_start", datetime.now())
        elapsed = int((datetime.now() - work_start).total_seconds())
        work_time = f"{elapsed // 3600:02d}:{(elapsed % 3600) // 60:02d}:{elapsed % 60:02d}"

        rows = [
            ("Разгрузок сегодня", str(self._stats.get("unload_count", 0))),
            ("Время работы",      work_time),
            ("Культура",          self._stats.get("culture", "—")),
        ]

        for label, value in rows:
            row_w = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setObjectName("menuSectionLabel")
            val = QLabel(value)
            val.setObjectName("menuStatValue")
            row_w.addWidget(lbl)
            row_w.addStretch()
            row_w.addWidget(val)
            bl.addLayout(row_w)
            bl.addSpacing(8)

            sep = QFrame()
            sep.setObjectName("menuSep")
            sep.setFixedHeight(1)
            bl.addWidget(sep)
            bl.addSpacing(16)

        bl.addStretch()
        vbox.addWidget(body, stretch=1)
        return page

    # ── Page 3: error history ─────────────────────────────────────────────

    def _page_errors(self) -> QWidget:
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._back_header("История ошибок"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(16, 8, 16, 8)
        il.setSpacing(2)

        max_e = self._config.error_history.get("max_entries", 20)
        errors = self._logger.read_errors(max_e)

        if not errors:
            empty = QLabel("Нет ошибок за сегодня")
            empty.setObjectName("menuSectionLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            il.addWidget(empty)
        else:
            # Header row
            hdr = QHBoxLayout()
            for txt, w in [("Время", 75), ("Датчик", 120), ("Статус", 110), ("Значение", 90)]:
                h = QLabel(txt)
                h.setFixedWidth(w)
                h.setObjectName("menuTableHeader")
                hdr.addWidget(h)
            hdr.addStretch()
            il.addLayout(hdr)

            sep = QFrame()
            sep.setObjectName("menuSep")
            sep.setFixedHeight(1)
            il.addWidget(sep)
            il.addSpacing(4)

            for entry in reversed(errors):
                ts = entry.get("timestamp", "")[-8:]
                sensor = _SENSOR_NAMES_RU.get(entry.get("sensor_name", ""), entry.get("sensor_name", ""))
                status = _STATUS_LABELS.get(entry.get("status", ""), entry.get("status", ""))
                value = f"{entry.get('value', '')} {entry.get('unit', '')}".strip()

                r = QHBoxLayout()
                r.setSpacing(0)
                for txt, w in [(ts, 75), (sensor, 120), (status, 110), (value, 90)]:
                    cell = QLabel(txt)
                    cell.setFixedWidth(w)
                    cell.setObjectName("menuTableRow")
                    r.addWidget(cell)
                r.addStretch()
                il.addLayout(r)

        il.addStretch()
        scroll.setWidget(inner)
        vbox.addWidget(scroll, stretch=1)
        return page

    # ── Page 4: shutdown ──────────────────────────────────────────────────

    def _page_shutdown(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 0, 32, 32)
        layout.setSpacing(20)
        layout.addStretch()

        lbl = QLabel("Выключить приложение?")
        lbl.setObjectName("menuPageTitle")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        layout.addSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        btn_yes = QPushButton("Да, выключить")
        btn_yes.setFixedHeight(58)
        btn_yes.setObjectName("menuDangerBtn")
        btn_yes.clicked.connect(self._do_shutdown)
        btn_row.addWidget(btn_yes)

        btn_no = QPushButton("Отмена")
        btn_no.setFixedHeight(58)
        btn_no.setObjectName("menuNavBtn")
        btn_no.clicked.connect(lambda: self._goto(_PAGE_MAIN))
        btn_row.addWidget(btn_no)

        layout.addLayout(btn_row)
        layout.addStretch()
        return page

    # ── Helpers ────────────────────────────────────────────────────────────

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("menuSectionLabel")
        return lbl

    # ── Actions ────────────────────────────────────────────────────────────

    def _on_theme(self, theme: str):
        self._theme = theme
        self.setStyleSheet(build_stylesheet(self._config, theme))
        self.theme_changed.emit(theme)

    def _on_culture(self, culture: str):
        self._stats["culture"] = culture
        self.culture_changed.emit(culture)

    def _on_window_mode(self, mode: str):
        self._config.set_and_save("ui.window_mode", mode)
        self.window_mode_changed.emit(mode)

    def _do_shutdown(self):
        self.accept()
        QApplication.instance().quit()
