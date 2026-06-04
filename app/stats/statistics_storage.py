from datetime import datetime
from pathlib import Path
from typing import Optional

from peewee import (
    CharField,
    DatabaseProxy,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
)

_proxy = DatabaseProxy()


class _Base(Model):
    class Meta:
        database = _proxy


class Session(_Base):
    date = CharField()
    start_time = DateTimeField()
    end_time = DateTimeField(null=True)
    status = CharField(default="active")  # active / closed / crashed
    duration_min = FloatField(default=0)
    threshing_min = FloatField(default=0)
    idle_min = FloatField(default=0)
    efficiency_pct = FloatField(default=0)
    unload_count = IntegerField(default=0)
    volume_m3 = FloatField(default=0)
    weight_kg = FloatField(default=0)
    avg_rpm_drum = FloatField(null=True)
    avg_rpm_kolosa = FloatField(null=True)
    avg_rpm_solomotryas = FloatField(null=True)
    avg_rpm_fan = FloatField(null=True)
    warn_count = IntegerField(default=0)
    error_count = IntegerField(default=0)
    last_updated = DateTimeField(null=True)

    class Meta:
        table_name = "sessions"


class SessionCulture(_Base):
    session = ForeignKeyField(Session, backref="cultures", on_delete="CASCADE")
    culture = CharField()
    unload_count = IntegerField(default=0)
    volume_m3 = FloatField(default=0)
    weight_kg = FloatField(default=0)
    time_start = DateTimeField(null=True)
    time_end = DateTimeField(null=True)

    class Meta:
        table_name = "session_cultures"


class ErrorEvent(_Base):
    session = ForeignKeyField(Session, backref="errors", on_delete="CASCADE")
    timestamp = DateTimeField()
    sensor_name = CharField()
    error_type = CharField()  # 'warn' | 'error'
    value = FloatField(null=True)
    threshold = FloatField(null=True)

    class Meta:
        table_name = "error_events"


class AppState(_Base):
    key = CharField(primary_key=True)
    value = CharField(null=True)

    class Meta:
        table_name = "app_state"


class StatisticsStorage:
    def __init__(self, data_dir: str):
        db_path = Path(data_dir) / "statistics.db"
        db_path.parent.mkdir(exist_ok=True)
        db = SqliteDatabase(
            str(db_path),
            pragmas={"journal_mode": "wal", "foreign_keys": 1},
        )
        _proxy.initialize(db)
        db.connect()
        db.create_tables([Session, SessionCulture, ErrorEvent, AppState], safe=True)

    def close(self):
        try:
            if not _proxy.obj.is_closed():
                _proxy.obj.close()
        except Exception:
            pass

    # ── AppState ──────────────────────────────────────────────────────────

    def get_state(self, key: str) -> Optional[str]:
        try:
            return AppState.get(AppState.key == key).value
        except AppState.DoesNotExist:
            return None

    def set_state(self, key: str, value: str):
        AppState.replace(key=key, value=value).execute()

    def clear_state(self, key: str):
        AppState.delete().where(AppState.key == key).execute()

    # ── Session ───────────────────────────────────────────────────────────

    def open_session(self, start: datetime) -> int:
        s = Session.create(
            date=start.strftime("%Y-%m-%d"),
            start_time=start,
            status="active",
            last_updated=start,
        )
        return s.id

    def update_session(self, session_id: int, **fields):
        Session.update(**fields, last_updated=datetime.now()).where(
            Session.id == session_id
        ).execute()

    def close_session(self, session_id: int, end: datetime):
        s = Session.get_by_id(session_id)
        dur = max((end - s.start_time).total_seconds() / 60, 0.0)
        eff = (s.threshing_min / dur * 100) if dur > 0 else 0.0
        Session.update(
            end_time=end,
            status="closed",
            duration_min=round(dur, 2),
            idle_min=round(max(dur - s.threshing_min, 0.0), 2),
            efficiency_pct=round(eff, 1),
            last_updated=end,
        ).where(Session.id == session_id).execute()

    def get_session(self, session_id: int) -> Optional[Session]:
        try:
            return Session.get_by_id(session_id)
        except Session.DoesNotExist:
            return None

    def get_sessions_for_date(self, date_str: str):
        return list(
            Session.select()
            .where(Session.date == date_str)
            .order_by(Session.start_time)
        )

    def get_all_sessions(self, limit: int = 20):
        return list(
            Session.select()
            .order_by(Session.start_time.desc())
            .limit(limit)
        )

    # ── SessionCulture ────────────────────────────────────────────────────

    def upsert_culture(
        self,
        session_id: int,
        culture: str,
        unload_count: int,
        volume_m3: float,
        weight_kg: float,
        time_start: Optional[datetime],
        time_end: Optional[datetime],
    ):
        try:
            sc = SessionCulture.get(
                (SessionCulture.session == session_id)
                & (SessionCulture.culture == culture)
            )
            SessionCulture.update(
                unload_count=unload_count,
                volume_m3=volume_m3,
                weight_kg=weight_kg,
                time_end=time_end,
            ).where(SessionCulture.id == sc.id).execute()
        except SessionCulture.DoesNotExist:
            SessionCulture.create(
                session=session_id,
                culture=culture,
                unload_count=unload_count,
                volume_m3=volume_m3,
                weight_kg=weight_kg,
                time_start=time_start,
                time_end=time_end,
            )

    def get_cultures_for_session(self, session_id: int):
        return list(
            SessionCulture.select().where(SessionCulture.session == session_id)
        )

    # ── ErrorEvent ────────────────────────────────────────────────────────

    def log_error_event(
        self,
        session_id: int,
        sensor_name: str,
        error_type: str,
        value: float,
        threshold: Optional[float],
    ):
        ErrorEvent.create(
            session=session_id,
            timestamp=datetime.now(),
            sensor_name=sensor_name,
            error_type=error_type,
            value=value,
            threshold=threshold,
        )

    def get_errors_for_session(self, session_id: int):
        return list(
            ErrorEvent.select()
            .where(ErrorEvent.session == session_id)
            .order_by(ErrorEvent.timestamp)
        )

    # ── Aggregation ───────────────────────────────────────────────────────

    def daily_summary(self, date_str: str) -> dict:
        sessions = list(
            Session.select().where(
                Session.date == date_str, Session.status != "active"
            )
        )
        dur = sum(s.duration_min for s in sessions)
        thresh = sum(s.threshing_min for s in sessions)
        eff = (thresh / dur * 100) if dur > 0 else 0.0

        culture_stats: dict = {}
        for s in sessions:
            for sc in SessionCulture.select().where(SessionCulture.session == s.id):
                c = sc.culture
                if c not in culture_stats:
                    culture_stats[c] = {"unload_count": 0, "volume_m3": 0.0, "weight_kg": 0.0}
                culture_stats[c]["unload_count"] += sc.unload_count
                culture_stats[c]["volume_m3"] += sc.volume_m3
                culture_stats[c]["weight_kg"] += sc.weight_kg

        return {
            "date": date_str,
            "session_count": len(sessions),
            "duration_min": dur,
            "threshing_min": thresh,
            "efficiency_pct": round(eff, 1),
            "unload_count": sum(s.unload_count for s in sessions),
            "weight_kg": sum(s.weight_kg for s in sessions),
            "warn_count": sum(s.warn_count for s in sessions),
            "error_count": sum(s.error_count for s in sessions),
            "cultures": culture_stats,
        }

    def season_summary(self, year: int) -> dict:
        sessions = list(
            Session.select().where(
                Session.date.startswith(str(year)), Session.status != "active"
            )
        )
        if not sessions:
            return {
                "year": year, "days_worked": 0, "threshing_hours": 0.0,
                "unload_count": 0, "weight_kg": 0.0, "cultures": {},
                "best_day": None, "best_day_weight_kg": 0.0,
            }

        days = {s.date for s in sessions}
        thresh_h = sum(s.threshing_min for s in sessions) / 60

        culture_stats: dict = {}
        for s in sessions:
            for sc in SessionCulture.select().where(SessionCulture.session == s.id):
                c = sc.culture
                if c not in culture_stats:
                    culture_stats[c] = {"unload_count": 0, "volume_m3": 0.0, "weight_kg": 0.0}
                culture_stats[c]["unload_count"] += sc.unload_count
                culture_stats[c]["volume_m3"] += sc.volume_m3
                culture_stats[c]["weight_kg"] += sc.weight_kg

        day_weights: dict = {}
        for s in sessions:
            day_weights[s.date] = day_weights.get(s.date, 0.0) + s.weight_kg
        best_day = max(day_weights, key=lambda d: day_weights[d]) if day_weights else None

        return {
            "year": year,
            "days_worked": len(days),
            "threshing_hours": round(thresh_h, 1),
            "unload_count": sum(s.unload_count for s in sessions),
            "weight_kg": sum(s.weight_kg for s in sessions),
            "cultures": culture_stats,
            "best_day": best_day,
            "best_day_weight_kg": day_weights.get(best_day, 0.0) if best_day else 0.0,
        }
