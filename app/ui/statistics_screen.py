from datetime import datetime
from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QScroller,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.config_loader import ConfigLoader
from app.stats.statistics_exporter import StatisticsExporter

_SENSOR_RU = {
    "drum": "Барабан",
    "kolosa": "Колос",
    "solomotryas": "Соломотряс",
    "fan_speed": "Вентилятор",
}

_TAB_SESSION = 0
_TAB_DAY = 1
_TAB_SEASON = 2


def _fmt_hhmm(minutes: float) -> str:
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h} ч {m:02d} мин"


def _fmt_dt(val) -> str:
    if val is None:
        return "—"
    if isinstance(val, str):
        try:
            val = datetime.fromisoformat(val)
        except (ValueError, TypeError):
            return str(val)
    return val.strftime("%d.%m  %H:%M")


def _fmt_tons(kg: float) -> str:
    return f"{kg / 1000:.1f} т"


def _fmt_rpm(val) -> str:
    return f"{round(val)} об/мин" if val is not None else "—"


class StatsPage(QWidget):
    def __init__(
        self,
        collector,
        config: ConfigLoader,
        back_fn: Callable,
        parent=None,
    ):
        super().__init__(parent)
        self._collector = collector
        self._config = config
        self._back_fn = back_fn
        self._exporter = StatisticsExporter(
            collector.storage,
            export_dir=config.logging_config.get("data_dir", "data") + "/export",
        )
        self._active_tab = _TAB_SESSION
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_tab_bar())

        self._content_stack = QStackedWidget()
        self._scroll_session = self._make_scroll()
        self._scroll_day = self._make_scroll()
        self._scroll_season = self._make_scroll()
        self._content_stack.addWidget(self._scroll_session)
        self._content_stack.addWidget(self._scroll_day)
        self._content_stack.addWidget(self._scroll_season)
        root.addWidget(self._content_stack, stretch=1)

    def _build_header(self) -> QWidget:
        hdr = QWidget()
        hdr.setObjectName("menuHeader")
        hdr.setFixedHeight(52)
        row = QHBoxLayout(hdr)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(8)

        from app.ui.app_icons import icon as ui_icon
        key = "colors_dark" if self._theme() == "dark" else "colors_light"
        primary = self._config.ui.get(key, {}).get("primary", "#1565C0")

        back = QPushButton()
        back.setIcon(ui_icon("back", color=primary))
        back.setObjectName("menuBackBtn")
        back.setFixedSize(46, 46)
        back.clicked.connect(self._back_fn)
        row.addWidget(back)

        title = QLabel("СТАТИСТИКА")
        title.setObjectName("menuPageTitle")
        row.addWidget(title, stretch=1)

        self._btn_export = QPushButton("Экспорт")
        self._btn_export.setObjectName("menuNavBtn")
        self._btn_export.setFixedHeight(38)
        self._btn_export.clicked.connect(self._on_export)
        row.addWidget(self._btn_export)

        return hdr

    def _build_tab_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("menuHeader")
        row = QHBoxLayout(bar)
        row.setContentsMargins(12, 6, 12, 6)
        row.setSpacing(6)

        group = QButtonGroup(self)
        group.setExclusive(True)
        for idx, label in [(_TAB_SESSION, "Сессия"), (_TAB_DAY, "День"), (_TAB_SEASON, "Сезон")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(idx == _TAB_SESSION)
            btn.setObjectName("menuToggleBtn")
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda _, i=idx: self._switch_tab(i))
            group.addButton(btn)
            row.addWidget(btn)

        return bar

    def _make_scroll(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setLayout(QVBoxLayout())
        inner.layout().setContentsMargins(16, 10, 16, 10)
        inner.layout().setSpacing(4)
        scroll.setWidget(inner)
        QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        return scroll

    # ── Tab switching ─────────────────────────────────────────────────────

    def _switch_tab(self, idx: int):
        self._active_tab = idx
        self._content_stack.setCurrentIndex(idx)
        self._rebuild_current_tab()

    def refresh(self):
        self._rebuild_current_tab()

    def _rebuild_current_tab(self):
        if self._active_tab == _TAB_SESSION:
            self._rebuild_session_tab()
        elif self._active_tab == _TAB_DAY:
            self._rebuild_day_tab()
        else:
            self._rebuild_season_tab()

    # ── Session tab ───────────────────────────────────────────────────────

    def _rebuild_session_tab(self):
        layout = self._clear_scroll(self._scroll_session)

        live = self._collector.get_live_session_data()
        if live:
            self._add_section(layout, f"Сессия  {_fmt_dt(live['start_time'])} — сейчас  [активна]")
            self._add_row(layout, "Продолжительность", _fmt_hhmm(live["duration_min"]))
            self._add_row(layout, "Молотьба", _fmt_hhmm(live["threshing_min"]))
            self._add_row(layout, "Простой", _fmt_hhmm(live["idle_min"]))
            self._add_row(layout, "КПД", f"{live['efficiency_pct']:.0f}%")
            self._add_sep(layout)
            self._add_row(layout, "Культура", live["culture"])
            self._add_row(layout, "Разгрузок", str(live["unload_count"]))
            self._add_row(layout, "Объём", f"{live['volume_m3']:.1f} м³")
            self._add_row(layout, "Вес", _fmt_tons(live["weight_kg"]))
            self._add_sep(layout)
            self._add_row(layout, "Барабан (ср.)", _fmt_rpm(live["avg_rpm_drum"]))
            self._add_row(layout, "Колос (ср.)", _fmt_rpm(live["avg_rpm_kolosa"]))
            self._add_row(layout, "Соломотряс (ср.)", _fmt_rpm(live["avg_rpm_solomotryas"]))
            self._add_row(layout, "Вентилятор (ср.)", _fmt_rpm(live["avg_rpm_fan"]))
            self._add_sep(layout)
            self._add_row(layout, "Предупреждений", str(live["warn_count"]))
            self._add_row(layout, "Ошибок", str(live["error_count"]))

            errors = self._collector.storage.get_errors_for_session(live["session_id"])
            if errors:
                self._add_sep(layout)
                for e in errors[-10:]:
                    ts = _fmt_dt(e.timestamp)
                    tag = "ОШИБ" if e.error_type == "error" else "ПРЕД"
                    sensor = _SENSOR_RU.get(e.sensor_name, e.sensor_name)
                    val = f"{round(e.value)} об/мин" if e.value is not None else ""
                    self._add_error_row(layout, ts, tag, sensor, val)

            self._add_sep(layout)
        else:
            self._add_section(layout, "Нет активной сессии")
            self._add_sep(layout)

        # Recent sessions list
        self._add_section(layout, "Последние сессии")
        past = self._collector.storage.get_all_sessions(limit=10)
        active_id = self._collector.session_id
        past = [s for s in past if s.id != active_id]
        if not past:
            layout.addWidget(self._make_label("Нет завершённых сессий", "menuSectionLabel"))
        else:
            for s in past:
                end_str = _fmt_dt(s.end_time) if s.end_time else "—"
                txt = (
                    f"{_fmt_dt(s.start_time)} – {end_str}   "
                    f"{s.unload_count} разгр   {_fmt_tons(s.weight_kg)}"
                )
                layout.addWidget(self._make_label(txt, "menuTableRow"))

        layout.addStretch()

    # ── Day tab ───────────────────────────────────────────────────────────

    def _rebuild_day_tab(self):
        layout = self._clear_scroll(self._scroll_day)
        today = datetime.now().strftime("%Y-%m-%d")
        summary = self._collector.storage.daily_summary(today)

        self._add_section(layout, datetime.now().strftime("%d.%m.%Y"))
        self._add_row(layout, "Сессий", str(summary["session_count"]))
        self._add_row(layout, "Время работы", _fmt_hhmm(summary["duration_min"]))
        self._add_row(layout, "Молотьба", _fmt_hhmm(summary["threshing_min"]))
        self._add_row(layout, "КПД", f"{summary['efficiency_pct']:.0f}%")
        self._add_sep(layout)
        self._add_row(layout, "Разгрузок", str(summary["unload_count"]))
        self._add_row(layout, "Убрано", _fmt_tons(summary["weight_kg"]))
        self._add_sep(layout)
        self._add_row(layout, "Предупреждений", str(summary["warn_count"]))
        self._add_row(layout, "Ошибок", str(summary["error_count"]))

        if summary["cultures"]:
            self._add_sep(layout)
            self._add_section(layout, "По культурам")
            for culture, data in summary["cultures"].items():
                self._add_row(
                    layout, culture,
                    f"{data['unload_count']} разгр  |  {_fmt_tons(data['weight_kg'])}"
                )

        layout.addStretch()

    # ── Season tab ────────────────────────────────────────────────────────

    def _rebuild_season_tab(self):
        layout = self._clear_scroll(self._scroll_season)
        year = datetime.now().year
        summary = self._collector.storage.season_summary(year)

        self._add_section(layout, f"Сезон {year}")
        self._add_row(layout, "Дней работы", str(summary["days_worked"]))
        self._add_row(layout, "Моточасов", f"{summary['threshing_hours']:.1f} ч")
        self._add_sep(layout)
        self._add_row(layout, "Разгрузок", str(summary["unload_count"]))
        self._add_row(layout, "Убрано", _fmt_tons(summary["weight_kg"]))

        if summary["best_day"]:
            try:
                bd = datetime.strptime(summary["best_day"], "%Y-%m-%d").strftime("%d.%m")
            except ValueError:
                bd = summary["best_day"]
            self._add_row(layout, "Лучший день", f"{bd}  —  {_fmt_tons(summary['best_day_weight_kg'])}")

        if summary["cultures"]:
            self._add_sep(layout)
            self._add_section(layout, "По культурам")
            for culture, data in summary["cultures"].items():
                self._add_row(
                    layout, culture,
                    f"{data['unload_count']} разгр  |  {_fmt_tons(data['weight_kg'])}"
                )

        layout.addStretch()

    # ── Export ────────────────────────────────────────────────────────────

    def _on_export(self):
        try:
            if self._active_tab == _TAB_SESSION:
                sid = self._collector.session_id
                if sid is None:
                    past = self._collector.storage.get_all_sessions(limit=1)
                    if not past:
                        QMessageBox.information(self, "Экспорт", "Нет данных для экспорта")
                        return
                    sid = past[0].id
                path = self._exporter.export_session(sid)
            elif self._active_tab == _TAB_DAY:
                today = datetime.now().strftime("%Y-%m-%d")
                path = self._exporter.export_day(today)
            else:
                path = self._exporter.export_season(datetime.now().year)

            QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{path}")
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка экспорта", str(exc))

    # ── Helpers ───────────────────────────────────────────────────────────

    def _theme(self) -> str:
        return self._config.ui.get("theme", "light")

    def _clear_scroll(self, scroll: QScrollArea) -> QVBoxLayout:
        inner = scroll.widget()
        old = inner.layout()
        while old.count():
            item = old.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        return old

    def _make_label(self, text: str, obj_name: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName(obj_name)
        lbl.setWordWrap(True)
        return lbl

    def _add_section(self, layout: QVBoxLayout, text: str):
        lbl = QLabel(text)
        lbl.setObjectName("menuTableHeader")
        layout.addWidget(lbl)
        layout.addSpacing(2)

    def _add_sep(self, layout: QVBoxLayout):
        sep = QFrame()
        sep.setObjectName("menuSep")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(4)

    def _add_row(self, layout: QVBoxLayout, label: str, value: str):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setObjectName("menuSectionLabel")
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        val = QLabel(value)
        val.setObjectName("menuStatValue")
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(lbl)
        row.addWidget(val)
        container = QWidget()
        container.setLayout(row)
        layout.addWidget(container)

    def _add_error_row(self, layout: QVBoxLayout, ts: str, tag: str, sensor: str, val: str):
        txt = f"  {ts}  [{tag}]  {sensor}  {val}"
        lbl = QLabel(txt)
        lbl.setObjectName("menuTableRow")
        layout.addWidget(lbl)
