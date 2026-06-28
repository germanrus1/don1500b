"""AppBridge — единая точка связи между Python-бэкендом и QML-фронтом."""
from datetime import datetime
from typing import Dict

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QVariant

from app.config.config_loader import ConfigLoader
from app.logger.data_logger import DataLogger
from app.sensors.sensor_base import SensorReading, SensorStatus

# ── Сенсоры: описание для отображения ──────────────────────────────────────

# MDI6 unicode символы для иконок (шрифт materialdesignicons6-webfont)
_I = {
    "engine":     "\U000f01fa",
    "thermometer":"\U000f050f",
    "gauge":      "\U000f029a",
    "gas-station":"\U000f0298",
    "bolt":       "\U000f140b",
    "rotate":     "\U000f0464",
    "transfer":   "\U000f0530",
    "fan":        "\U000f0210",
    "water":      "\U000f058c",
    "grain":      "\U000f0d7c",
    "menu":       "\U000f035c",
    "close":      "\U000f0156",
    "back":       "\U000f004d",
    "check":      "\U000f05e0",
    "power":      "\U000f0425",
    "power-set":  "\U000f0426",
    "leaf":       "\U000f032a",
    "radar":      "\U000f0437",
    "contrast":   "\U000f0195",
    "chart-bar":  "\U000f0128",
    "download":   "\U000f01da",
    "sun":        "\U000f05a8",
    "moon":       "\U000f0594",
    # Культуры
    "barley":     "\U000f0073",
    "corn":       "\U000f07b8",
    "flower":     "\U000f024a",
    "sprout":     "\U000f0e66",
    "seed":       "\U000f0e62",
    "nature":     "\U000f038e",
}

# Метаданные культур: иконка и цвет для каждой
CROP_META = {
    "Пшеница":     {"icon": _I["barley"], "color": "#e8a020"},
    "Ячмень":      {"icon": _I["barley"], "color": "#c49a30"},
    "Рожь":        {"icon": _I["grain"],  "color": "#9a6a30"},
    "Овёс":        {"icon": _I["seed"],   "color": "#c4a060"},
    "Кукуруза":    {"icon": _I["corn"],   "color": "#f0c010"},
    "Подсолнечник":{"icon": _I["flower"], "color": "#f5b010"},
    "Рапс":        {"icon": _I["sprout"], "color": "#a8c020"},
    "Гречиха":     {"icon": _I["seed"],   "color": "#c08040"},
    "Горох":       {"icon": _I["sprout"], "color": "#60a820"},
    "Фацелия":     {"icon": _I["flower"], "color": "#6060d0"},
    "Эспарцет":    {"icon": _I["nature"], "color": "#c03030"},
}

SENSOR_META = {
    "erpm":  {"short": "Двигатель",     "full": "Обороты двигателя",                "unit": "об/мин", "icon": _I["engine"],      "color": "#7c5cf0", "side": "left"},
    "etemp": {"short": "Темп. двигат.", "full": "Температура охлаждающей жидкости", "unit": "°C",     "icon": _I["thermometer"], "color": "#e85d3a", "side": "left"},
    "oil":   {"short": "Давл. масла",   "full": "Давление масла",                   "unit": "бар",    "icon": _I["gauge"],       "color": "#5b6ef0", "side": "left"},
    "fuel":  {"short": "Топливо",       "full": "Уровень топлива в баке",           "unit": "%",      "icon": _I["gas-station"], "color": "#f0871a", "side": "left"},
    "volt":  {"short": "Бортсеть",      "full": "Напряжение бортовой сети",         "unit": "В",      "icon": _I["bolt"],        "color": "#e0930f", "side": "left"},
    "drum":  {"short": "Барабан",       "full": "Частота молотильного барабана",    "unit": "об/мин", "icon": _I["rotate"],      "color": "#3b82f6", "side": "right"},
    "auger": {"short": "Колос. шнек",  "full": "Обороты колосового шнека",         "unit": "об/мин", "icon": _I["transfer"],    "color": "#22a05a", "side": "right"},
    "fan":   {"short": "Вентилятор",    "full": "Вентилятор системы очистки",       "unit": "об/мин", "icon": _I["fan"],         "color": "#0ea5b5", "side": "right"},
    "moist": {"short": "Влажность",     "full": "Влажность зерна",                  "unit": "%",      "icon": _I["water"],       "color": "#14a08a", "side": "right"},
    "loss":  {"short": "Потери зерна",  "full": "Потери зерна за молотилкой",       "unit": "%",      "icon": _I["grain"],       "color": "#d6479b", "side": "right"},
}

LEFT_SENSORS  = [k for k, v in SENSOR_META.items() if v["side"] == "left"]
RIGHT_SENSORS = [k for k, v in SENSOR_META.items() if v["side"] == "right"]

# Маппинг: имя GPIO-датчика → display ID
HW_ALIAS: Dict[str, str] = {
    "drum":      "drum",
    "kolosa":    "auger",
    "fan_speed": "fan",
}

# ── Токены дизайна ──────────────────────────────────────────────────────────

_LIGHT = {
    "bg": "#eef1f5", "surface": "#ffffff", "menuBg": "#ffffff",
    "textPrimary": "#192230", "textSecondary": "#5d6b7e",
    "primary": "#1f6feb", "onPrimary": "#ffffff",
    "border": "#e1e6ee", "critical": "#d92d20", "warning": "#e8830c",
}
_DARK = {
    "bg": "#1b2634", "surface": "#27323f", "menuBg": "#202b3a",
    "textPrimary": "#f1f5fa", "textSecondary": "#a4b2c4",
    "primary": "#5b9bff", "onPrimary": "#0a1018",
    "border": "#3a4655", "critical": "#ff6157", "warning": "#ffb13b",
}


class AppBridge(QObject):
    """Единый Python-объект, доступный из QML через контекстное свойство 'bridge'."""

    # ── Сигналы ────────────────────────────────────────────────────────────
    themeChanged       = pyqtSignal()
    cultureChanged     = pyqtSignal()
    sensorsUpdated     = pyqtSignal()
    faultsUpdated      = pyqtSignal()
    speedChanged       = pyqtSignal()
    windowModeChanged  = pyqtSignal()
    enabledChanged     = pyqtSignal()
    headerWidthChanged = pyqtSignal()

    def __init__(self, config: ConfigLoader, logger: DataLogger,
                 collector=None, parent=None):
        super().__init__(parent)
        self._config    = config
        self._logger    = logger
        self._collector = collector
        self._theme     = config.ui.get("theme", "light")
        self._culture   = config.interface.get("cultures", ["Пшеница"])[0]
        self._speed     = 0.0
        self._header_width_m = float(config.get("harvest.header_width_m", 6.0))
        self._unload_count = 0
        self._work_start   = datetime.now()

        # Значения и состояния датчиков
        self._values: Dict[str, float] = {}
        self._states: Dict[str, str]   = {}   # "" | "warning" | "critical"
        self._faults: list             = []    # [{id, level, short, full}]

        # Включённость датчиков (загружается из config)
        saved = config.ui.get("sensors_enabled", {})
        self._enabled_sensors: Dict[str, bool] = {
            sid: bool(saved.get(sid, True)) for sid in SENSOR_META
        }

    # ── Тема ───────────────────────────────────────────────────────────────

    @pyqtProperty("QVariantMap", notify=themeChanged)
    def tokens(self) -> dict:
        return _DARK if self._theme == "dark" else _LIGHT

    @pyqtProperty(str, notify=themeChanged)
    def theme(self) -> str:
        return self._theme

    @pyqtSlot(str)
    def setTheme(self, theme: str):
        if self._theme != theme:
            self._theme = theme
            self._config.set_and_save("ui.theme", theme)
            self.themeChanged.emit()

    # ── Культура ───────────────────────────────────────────────────────────

    @pyqtProperty(str, notify=cultureChanged)
    def culture(self) -> str:
        return self._culture

    @pyqtProperty("QVariantList", constant=True)
    def cultures(self) -> list:
        return self._config.interface.get("cultures", ["Пшеница"])

    @pyqtProperty("QVariantList", constant=True)
    def cropItems(self) -> list:
        """Список культур с иконками и цветами для отображения в меню."""
        result = []
        for name in self._config.interface.get("cultures", ["Пшеница"]):
            meta = CROP_META.get(name, {"icon": _I["grain"], "color": "#888888"})
            result.append({"name": name, "icon": meta["icon"], "color": meta["color"]})
        return result

    @pyqtSlot(str)
    def setCulture(self, name: str):
        if self._culture != name:
            self._culture = name
            self.cultureChanged.emit()

    # ── Датчики ────────────────────────────────────────────────────────────

    @pyqtProperty("QVariantMap", notify=enabledChanged)
    def enabledSensors(self) -> dict:
        return dict(self._enabled_sensors)

    @pyqtSlot(str, bool)
    def setSensorEnabled(self, sid: str, enabled: bool):
        if sid in SENSOR_META and self._enabled_sensors.get(sid) != enabled:
            self._enabled_sensors[sid] = enabled
            self._config.set_and_save(f"ui.sensors_enabled.{sid}", enabled)
            self.enabledChanged.emit()

    @pyqtProperty("QVariantList", notify=enabledChanged)
    def leftSensors(self) -> list:
        return [self._sensor_item(sid) for sid in LEFT_SENSORS
                if self._enabled_sensors.get(sid, True)]

    @pyqtProperty("QVariantList", notify=enabledChanged)
    def rightSensors(self) -> list:
        return [self._sensor_item(sid) for sid in RIGHT_SENSORS
                if self._enabled_sensors.get(sid, True)]

    @pyqtProperty("QVariantList", notify=sensorsUpdated)
    def sensorValues(self) -> list:
        """Возвращает список {id, value, state, display} для всех датчиков."""
        result = []
        for sid in list(SENSOR_META.keys()):
            meta = SENSOR_META[sid]
            raw  = self._values.get(sid)
            if raw is None:
                display = "—"
            elif raw == int(raw):
                display = str(int(raw))
            else:
                display = f"{raw:.1f}"
            result.append({
                "id":      sid,
                "value":   self._values.get(sid, 0.0),
                "state":   self._states.get(sid, ""),
                "display": display,
                "unit":    meta["unit"],
                "short":   meta["short"],
                "full":    meta["full"],
                "icon":    meta["icon"],
                "color":   meta["color"],
            })
        return result

    @pyqtProperty("QVariantList", notify=faultsUpdated)
    def faults(self) -> list:
        return self._faults

    @pyqtProperty(float, notify=speedChanged)
    def speed(self) -> float:
        return self._speed

    # ── Жатка / площадь ────────────────────────────────────────────────────

    @pyqtProperty(float, notify=headerWidthChanged)
    def headerWidth(self) -> float:
        return self._header_width_m

    @pyqtSlot(float)
    def setHeaderWidth(self, width_m: float):
        width_m = round(width_m, 2)
        if width_m > 0 and self._header_width_m != width_m:
            self._header_width_m = width_m
            self._config.set_and_save("harvest.header_width_m", width_m)
            if self._collector:
                self._collector.set_header_width(width_m)
            self.headerWidthChanged.emit()

    # ── Слоты от сенсор-контроллера ────────────────────────────────────────

    @pyqtSlot(dict)
    def onSensorUpdate(self, readings: Dict[str, SensorReading]):
        speed_reading = readings.get("speed")
        if speed_reading is not None and speed_reading.value != self._speed:
            self._speed = speed_reading.value
            self.speedChanged.emit()

        new_faults = []
        for hw_name, reading in readings.items():
            did = HW_ALIAS.get(hw_name, hw_name)
            if did not in SENSOR_META:
                continue
            state = (
                "critical" if reading.status == SensorStatus.CRITICAL
                else "warning" if reading.has_error
                else ""
            )
            self._values[did] = reading.value
            self._states[did] = state
            if reading.has_error:
                meta = SENSOR_META[did]
                new_faults.append({
                    "id":    did,
                    "level": state,
                    "short": meta["short"],
                    "full":  meta["full"],
                    "icon":  meta["icon"],
                    "color": meta["color"],
                })

        self.sensorsUpdated.emit()

        if new_faults != self._faults:
            self._faults = new_faults
            self.faultsUpdated.emit()

    @pyqtSlot(int)
    def onUnload(self, count: int):
        self._unload_count = count
        self._logger.log_unload(count, self._culture)

    # ── Настройки ──────────────────────────────────────────────────────────

    @pyqtSlot(str)
    def setWindowMode(self, mode: str):
        self._config.set_and_save("ui.window_mode", mode)
        self.windowModeChanged.emit()

    @pyqtProperty(str, notify=windowModeChanged)
    def windowMode(self) -> str:
        return self._config.ui.get("window_mode", "windowed")

    # ── Статистика ─────────────────────────────────────────────────────────

    @pyqtProperty("QVariantMap", notify=sensorsUpdated)
    def statsSession(self) -> dict:
        """Текущая сессия — обновляется в реальном времени."""
        elapsed_min = int((datetime.now() - self._work_start).total_seconds() / 60)
        h, m = elapsed_min // 60, elapsed_min % 60
        base = {
            "workTime":  f"{h} ч {m:02d} мин",
            "culture":   self._culture,
            "unloads":   str(self._unload_count),
            "weightKg":  "—",
            "efficiency":"—",
            "warnCount": "—",
            "areaHa":    "—",
        }
        if self._collector:
            try:
                s = self._collector.get_live_session_data()
                wkg = s.get("weight_kg", 0.0)
                base["weightKg"]  = f"{wkg:.0f}" if wkg else "—"
                base["efficiency"]= f"{s.get('efficiency_pct', 0):.0f}%"
                base["warnCount"] = str(s.get("warn_count", 0))
                area = s.get("area_ha", 0.0)
                base["areaHa"]    = f"{area:.2f} га" if area else "—"
                tm = s.get("threshing_min", 0)
                th, tm2 = int(tm // 60), int(tm % 60)
                base["threshTime"]= f"{th} ч {tm2:02d} мин"
            except Exception:
                pass
        return base

    @pyqtProperty("QVariantMap", notify=sensorsUpdated)
    def statsDay(self) -> dict:
        """Данные за сегодняшний день из базы данных."""
        today = datetime.now().strftime("%Y-%m-%d")
        if not self._collector:
            return {"date": today, "sessions": "0", "workTime": "—",
                    "unloads": "0", "weightKg": "—", "efficiency": "—", "areaHa": "—"}
        try:
            s = self._collector._storage.daily_summary(today)
            dur = s.get("duration_min", 0)
            h, m = int(dur // 60), int(dur % 60)
            wkg = s.get("weight_kg", 0.0)
            eff = s.get("efficiency_pct", 0)
            area = s.get("area_ha", 0.0)
            return {
                "date":      datetime.now().strftime("%d.%m.%Y"),
                "sessions":  str(s.get("session_count", 0)),
                "workTime":  f"{h} ч {m:02d} мин",
                "unloads":   str(s.get("unload_count", 0)),
                "weightKg":  f"{wkg:.0f} кг" if wkg else "—",
                "efficiency":f"{eff:.0f}%" if eff else "—",
                "errors":    str(s.get("error_count", 0)),
                "areaHa":    f"{area:.2f} га" if area else "—",
            }
        except Exception:
            return {"date": today, "sessions": "—", "workTime": "—",
                    "unloads": "—", "weightKg": "—", "efficiency": "—", "errors": "—", "areaHa": "—"}

    @pyqtProperty("QVariantMap", notify=sensorsUpdated)
    def statsSeason(self) -> dict:
        """Данные за текущий сезон (год) из базы данных."""
        year = datetime.now().year
        if not self._collector:
            return {"year": str(year), "days": "0", "threshHours": "—",
                    "unloads": "0", "weightT": "—", "bestDay": "—", "areaHa": "—"}
        try:
            s = self._collector._storage.season_summary(year)
            wkg = s.get("weight_kg", 0.0)
            area = s.get("area_ha", 0.0)
            best = s.get("best_day", "")
            if best:
                try:
                    from datetime import datetime as dt
                    best = dt.strptime(best, "%Y-%m-%d").strftime("%d.%m")
                except Exception:
                    pass
            return {
                "year":        str(year),
                "days":        str(s.get("days_worked", 0)),
                "threshHours": f"{s.get('threshing_hours', 0):.1f} ч",
                "unloads":     str(s.get("unload_count", 0)),
                "weightT":     f"{wkg/1000:.1f} т" if wkg else "—",
                "bestDay":     best or "—",
                "bestDayKg":   f"{s.get('best_day_weight_kg', 0):.0f} кг"
                               if s.get("best_day_weight_kg") else "—",
                "areaHa":      f"{area:.1f} га" if area else "—",
            }
        except Exception:
            return {"year": str(year), "days": "—", "threshHours": "—",
                    "unloads": "—", "weightT": "—", "bestDay": "—", "bestDayKg": "—", "areaHa": "—"}

    # ── Навигационные карточки меню ────────────────────────────────────────

    @pyqtProperty("QVariantList", constant=True)
    def navItems(self) -> list:
        return [
            {"icon": _I["leaf"],      "label": "Культура",   "color": "#22a05a", "page": 1, "danger": False},
            {"icon": _I["radar"],     "label": "Датчики",    "color": "#3b82f6", "page": 2, "danger": False},
            {"icon": _I["contrast"],  "label": "Тема",       "color": "#7c5cf0", "page": 3, "danger": False},
            {"icon": _I["chart-bar"], "label": "Статистика", "color": "#f0871a", "page": 4, "danger": False},
            {"icon": _I["power-set"], "label": "Выключить",  "color": "#d92d20", "page": 5, "danger": True},
        ]

    @pyqtProperty("QVariantMap", constant=True)
    def uiIcons(self) -> dict:
        """Часто используемые иконки для QML: меню, назад, закрыть и т.д."""
        return {
            "menu":     _I["menu"],
            "close":    _I["close"],
            "back":     _I["back"],
            "check":    _I["check"],
            "power":    _I["power-set"],
            "sun":      _I["sun"],
            "moon":     _I["moon"],
            "download": _I["download"],
            "leaf":     _I["leaf"],
        }

    # ── Действия ───────────────────────────────────────────────────────────

    @pyqtSlot()
    def shutdown(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()

    # ── Вспомогательные ────────────────────────────────────────────────────

    @staticmethod
    def _sensor_item(sid: str) -> dict:
        m = SENSOR_META[sid]
        return {"id": sid, "short": m["short"], "full": m["full"],
                "unit": m["unit"], "icon": m["icon"], "color": m["color"]}
