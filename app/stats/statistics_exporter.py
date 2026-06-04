import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.stats.statistics_storage import StatisticsStorage


def _fmt_dt(val) -> str:
    if val is None:
        return ""
    if isinstance(val, str):
        try:
            val = datetime.fromisoformat(val)
        except (ValueError, TypeError):
            return str(val)
    return val.strftime("%d.%m.%Y %H:%M")


def _fmt_rpm(val) -> str:
    return str(round(val)) if val is not None else "—"


def _fmt_hhmm(minutes: float) -> str:
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h} ч {m:02d} мин"


class StatisticsExporter:
    def __init__(self, storage: StatisticsStorage, export_dir: str = "data/export"):
        self._storage = storage
        self._dir = Path(export_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def export_session(self, session_id: int) -> str:
        session = self._storage.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        start_str = (
            datetime.fromisoformat(str(session.start_time)).strftime("%Y-%m-%d_%H-%M")
            if session.start_time else "unknown"
        )
        filepath = self._dir / f"session_{start_str}.csv"

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Поле", "Значение"])
            w.writerow(["Дата", session.date])
            w.writerow(["Начало", _fmt_dt(session.start_time)])
            w.writerow(["Конец", _fmt_dt(session.end_time) if session.end_time else "активна"])
            w.writerow(["Продолжительность", _fmt_hhmm(session.duration_min)])
            w.writerow(["Молотьба", _fmt_hhmm(session.threshing_min)])
            w.writerow(["Простой", _fmt_hhmm(session.idle_min)])
            w.writerow(["КПД (%)", session.efficiency_pct])
            w.writerow(["Разгрузок", session.unload_count])
            w.writerow(["Объём (м³)", round(session.volume_m3, 1)])
            w.writerow(["Вес (кг)", round(session.weight_kg, 1)])
            w.writerow(["Ср. об/мин барабан", _fmt_rpm(session.avg_rpm_drum)])
            w.writerow(["Ср. об/мин колос", _fmt_rpm(session.avg_rpm_kolosa)])
            w.writerow(["Ср. об/мин соломотряс", _fmt_rpm(session.avg_rpm_solomotryas)])
            w.writerow(["Ср. об/мин вентилятор", _fmt_rpm(session.avg_rpm_fan)])
            w.writerow(["Предупреждений", session.warn_count])
            w.writerow(["Ошибок", session.error_count])
            w.writerow([])

            cultures = self._storage.get_cultures_for_session(session_id)
            if cultures:
                w.writerow(["Культура", "Разгрузок", "Объём (м³)", "Вес (кг)"])
                for sc in cultures:
                    w.writerow([sc.culture, sc.unload_count,
                                 round(sc.volume_m3, 1), round(sc.weight_kg, 1)])
                w.writerow([])

            errors = self._storage.get_errors_for_session(session_id)
            if errors:
                w.writerow(["Время", "Датчик", "Тип", "Значение", "Порог"])
                for e in errors:
                    w.writerow([
                        _fmt_dt(e.timestamp), e.sensor_name, e.error_type,
                        round(e.value, 1) if e.value is not None else "",
                        round(e.threshold, 1) if e.threshold is not None else "",
                    ])

        return str(filepath)

    def export_day(self, date_str: str) -> str:
        filepath = self._dir / f"day_{date_str}.csv"
        summary = self._storage.daily_summary(date_str)

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Поле", "Значение"])
            w.writerow(["Дата", date_str])
            w.writerow(["Сессий", summary["session_count"]])
            w.writerow(["Время работы", _fmt_hhmm(summary["duration_min"])])
            w.writerow(["Молотьба", _fmt_hhmm(summary["threshing_min"])])
            w.writerow(["КПД (%)", summary["efficiency_pct"]])
            w.writerow(["Разгрузок", summary["unload_count"]])
            w.writerow(["Вес (кг)", round(summary["weight_kg"], 1)])
            w.writerow(["Предупреждений", summary["warn_count"]])
            w.writerow(["Ошибок", summary["error_count"]])
            w.writerow([])

            if summary["cultures"]:
                w.writerow(["Культура", "Разгрузок", "Объём (м³)", "Вес (кг)"])
                for culture, data in summary["cultures"].items():
                    w.writerow([culture, data["unload_count"],
                                 round(data["volume_m3"], 1), round(data["weight_kg"], 1)])
                w.writerow([])

            sessions = self._storage.get_sessions_for_date(date_str)
            if sessions:
                w.writerow(["Начало", "Конец", "Молотьба", "Разгрузок", "Вес (кг)", "КПД (%)"])
                for s in sessions:
                    w.writerow([
                        _fmt_dt(s.start_time),
                        _fmt_dt(s.end_time) if s.end_time else "активна",
                        _fmt_hhmm(s.threshing_min),
                        s.unload_count,
                        round(s.weight_kg, 1),
                        s.efficiency_pct,
                    ])

        return str(filepath)

    def export_season(self, year: int) -> str:
        filepath = self._dir / f"season_{year}.csv"
        summary = self._storage.season_summary(year)

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Поле", "Значение"])
            w.writerow(["Сезон", year])
            w.writerow(["Дней работы", summary["days_worked"]])
            w.writerow(["Моточасов молотьбы", summary["threshing_hours"]])
            w.writerow(["Разгрузок", summary["unload_count"]])
            w.writerow(["Вес (кг)", round(summary["weight_kg"], 1)])
            if summary["best_day"]:
                w.writerow([
                    "Лучший день", summary["best_day"],
                    round(summary["best_day_weight_kg"] / 1000, 2), "т",
                ])
            w.writerow([])

            if summary["cultures"]:
                w.writerow(["Культура", "Разгрузок", "Объём (м³)", "Тонн"])
                for culture, data in summary["cultures"].items():
                    w.writerow([
                        culture, data["unload_count"],
                        round(data["volume_m3"], 1),
                        round(data["weight_kg"] / 1000, 2),
                    ])

        return str(filepath)

    def get_export_path(self, export_type: str, identifier) -> Optional[str]:
        """Convenience: export_type='session'|'day'|'season', identifier=session_id|date_str|year."""
        try:
            if export_type == "session":
                return self.export_session(int(identifier))
            elif export_type == "day":
                return self.export_day(str(identifier))
            elif export_type == "season":
                return self.export_season(int(identifier))
        except Exception as exc:
            print(f"[Exporter] Error: {exc}")
        return None
