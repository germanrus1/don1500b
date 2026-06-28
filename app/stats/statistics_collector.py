import time
from datetime import datetime
from typing import Dict, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSlot

from app.config.config_loader import ConfigLoader
from app.sensors.sensor_base import SensorStatus
from app.stats.statistics_storage import StatisticsStorage

_IMPULSE_SENSORS = ("drum", "kolosa", "solomotryas", "fan_speed")


class _RpmAccumulator:
    """Cumulative sum+count per sensor — only during active threshing."""

    def __init__(self):
        self._sum: Dict[str, float] = {s: 0.0 for s in _IMPULSE_SENSORS}
        self._count: Dict[str, int] = {s: 0 for s in _IMPULSE_SENSORS}

    def add(self, sensor: str, rpm: float):
        if sensor in self._sum:
            self._sum[sensor] += rpm
            self._count[sensor] += 1

    def averages(self) -> Dict[str, Optional[float]]:
        return {
            s: (self._sum[s] / self._count[s]) if self._count[s] > 0 else None
            for s in _IMPULSE_SENSORS
        }

    def reset(self):
        for s in _IMPULSE_SENSORS:
            self._sum[s] = 0.0
            self._count[s] = 0


class StatisticsCollector(QObject):
    def __init__(self, config: ConfigLoader, storage: StatisticsStorage):
        super().__init__()
        self._config = config
        self._storage = storage

        stats_cfg = config.stats
        self._bin_volume: float = stats_cfg.get("bin_volume_m3", 6.0)
        self._session_timeout_min: int = stats_cfg.get("session_timeout_min", 30)
        self._heartbeat_sec: int = stats_cfg.get("heartbeat_interval_sec", 60)

        self._densities: Dict[str, float] = {
            name: cfg.get("density", 0.7)
            for name, cfg in config.cultures_config.items()
        }

        drum_cfg = config.sensors.get("list", {}).get("drum", {})
        self._drum_threshold: float = drum_cfg.get("error_threshold_low", 100)

        harvest_cfg = config.get("harvest", {}) or {}
        self._header_width_m: float = harvest_cfg.get("header_width_m", 6.0)

        # Session state
        self._session_id: Optional[int] = None
        self._session_start: Optional[datetime] = None
        self._engine_running: bool = False

        # Time tracking (monotonic, not persisted directly)
        self._threshing_start: Optional[float] = None
        self._threshing_sec: float = 0.0
        self._last_speed_mono: Optional[float] = None

        # In-memory counters (written to DB on heartbeat and at session close)
        self._unload_count: int = 0
        self._volume_m3: float = 0.0
        self._weight_kg: float = 0.0
        self._area_m2: float = 0.0
        self._warn_count: int = 0
        self._error_count: int = 0

        # Current culture tracking
        self._culture: str = config.interface.get("cultures", ["Пшеница"])[0]
        self._culture_start: Optional[datetime] = None
        self._culture_unloads: int = 0
        self._culture_volume: float = 0.0
        self._culture_weight: float = 0.0
        self._culture_area_m2: float = 0.0

        self._prev_statuses: Dict[str, SensorStatus] = {}
        self._accum = _RpmAccumulator()

        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.timeout.connect(self._heartbeat)
        self._heartbeat_timer.start(self._heartbeat_sec * 1000)

        self._engine_timeout_timer = QTimer(self)
        self._engine_timeout_timer.setSingleShot(True)
        self._engine_timeout_timer.timeout.connect(self._on_engine_timeout)

        self._restore_session()

    # ── Session lifecycle ─────────────────────────────────────────────────

    def _restore_session(self):
        sid_str = self._storage.get_state("current_session_id")
        if not sid_str:
            return
        session_id = int(sid_str)
        session = self._storage.get_session(session_id)
        if not session or session.status != "active":
            self._clear_session_state()
            return

        engine_stop_str = self._storage.get_state("engine_stop_time")
        now = datetime.now()

        if engine_stop_str:
            try:
                engine_stop = datetime.fromisoformat(engine_stop_str)
            except ValueError:
                self._clear_session_state()
                return
            elapsed_min = (now - engine_stop).total_seconds() / 60
            if elapsed_min >= self._session_timeout_min:
                self._load_session_from_db(session_id, session)
                self._close_session(end_time=engine_stop)
                return
            remaining_ms = int((self._session_timeout_min * 60 - elapsed_min * 60) * 1000)
            self._load_session_from_db(session_id, session)
            self._engine_timeout_timer.start(max(1000, remaining_ms))
            print(f"[Stats] Resumed session {session_id}, grace {remaining_ms // 1000}s left")
        else:
            # Engine was running at crash — use last_updated as reference
            last_updated = session.last_updated
            if last_updated is None:
                last_updated = now
            if isinstance(last_updated, str):
                try:
                    last_updated = datetime.fromisoformat(last_updated)
                except ValueError:
                    last_updated = now
            elapsed_min = (now - last_updated).total_seconds() / 60
            if elapsed_min >= self._session_timeout_min:
                self._load_session_from_db(session_id, session)
                self._close_session(end_time=last_updated)
                return
            remaining_ms = int((self._session_timeout_min * 60 - elapsed_min * 60) * 1000)
            self._load_session_from_db(session_id, session)
            self._engine_timeout_timer.start(max(1000, remaining_ms))
            print(f"[Stats] Restored crashed session {session_id}")

    def _load_session_from_db(self, session_id: int, session):
        self._session_id = session_id
        self._session_start = (
            datetime.fromisoformat(str(session.start_time))
            if isinstance(session.start_time, str)
            else session.start_time
        )
        self._threshing_sec = float(
            self._storage.get_state("threshing_seconds") or 0
        )
        self._unload_count = session.unload_count
        self._volume_m3 = session.volume_m3
        self._weight_kg = session.weight_kg
        self._area_m2 = session.area_ha * 10000
        self._warn_count = session.warn_count
        self._error_count = session.error_count
        self._culture = (
            self._storage.get_state("current_culture") or self._culture
        )
        # Restore current culture counts from DB
        for sc in self._storage.get_cultures_for_session(session_id):
            if sc.culture == self._culture:
                self._culture_unloads = sc.unload_count
                self._culture_volume = sc.volume_m3
                self._culture_weight = sc.weight_kg
                self._culture_area_m2 = sc.area_ha * 10000
                break

    def _open_session(self):
        now = datetime.now()
        self._session_start = now
        self._threshing_sec = 0.0
        self._threshing_start = None
        self._unload_count = 0
        self._volume_m3 = 0.0
        self._weight_kg = 0.0
        self._area_m2 = 0.0
        self._warn_count = 0
        self._error_count = 0
        self._culture_start = now
        self._culture_unloads = 0
        self._culture_volume = 0.0
        self._culture_weight = 0.0
        self._culture_area_m2 = 0.0
        self._last_speed_mono = None
        self._accum.reset()
        self._prev_statuses.clear()

        self._session_id = self._storage.open_session(now)
        self._storage.set_state("current_session_id", str(self._session_id))
        self._storage.set_state("threshing_seconds", "0")
        self._storage.set_state("current_culture", self._culture)
        print(f"[Stats] Session {self._session_id} opened at {now:%H:%M:%S}")

    def _close_session(self, end_time: Optional[datetime] = None):
        if self._session_id is None:
            return
        end_time = end_time or datetime.now()

        if self._threshing_start is not None:
            self._threshing_sec += time.monotonic() - self._threshing_start
            self._threshing_start = None

        self._flush_culture(end_time)

        avgs = self._accum.averages()
        self._storage.update_session(
            self._session_id,
            threshing_min=round(self._threshing_sec / 60, 2),
            unload_count=self._unload_count,
            volume_m3=round(self._volume_m3, 2),
            weight_kg=round(self._weight_kg, 2),
            area_ha=round(self._area_m2 / 10000, 3),
            warn_count=self._warn_count,
            error_count=self._error_count,
            avg_rpm_drum=avgs.get("drum"),
            avg_rpm_kolosa=avgs.get("kolosa"),
            avg_rpm_solomotryas=avgs.get("solomotryas"),
            avg_rpm_fan=avgs.get("fan_speed"),
        )
        self._storage.close_session(self._session_id, end_time)
        self._clear_session_state()
        print(f"[Stats] Session {self._session_id} closed at {end_time:%H:%M:%S}")

        self._session_id = None
        self._session_start = None
        self._threshing_sec = 0.0
        self._unload_count = 0
        self._volume_m3 = 0.0
        self._weight_kg = 0.0
        self._area_m2 = 0.0
        self._warn_count = 0
        self._error_count = 0
        self._accum.reset()

    def _clear_session_state(self):
        for key in ("current_session_id", "engine_stop_time", "threshing_seconds", "current_culture"):
            self._storage.clear_state(key)

    # ── Engine state ──────────────────────────────────────────────────────

    def _on_engine_started(self):
        self._engine_running = True
        if self._engine_timeout_timer.isActive():
            self._engine_timeout_timer.stop()
        self._storage.clear_state("engine_stop_time")
        if self._session_id is None:
            self._open_session()

    def _on_engine_stopped(self):
        self._engine_running = False
        stop_time = datetime.now()
        self._storage.set_state("engine_stop_time", stop_time.isoformat())
        self._engine_timeout_timer.start(self._session_timeout_min * 60 * 1000)

    def _on_engine_timeout(self):
        engine_stop_str = self._storage.get_state("engine_stop_time")
        end_time = datetime.now()
        if engine_stop_str:
            try:
                end_time = datetime.fromisoformat(engine_stop_str)
            except ValueError:
                pass
        self._close_session(end_time=end_time)

    # ── Heartbeat ─────────────────────────────────────────────────────────

    def _heartbeat(self):
        if self._session_id is None:
            return

        if self._threshing_start is not None:
            elapsed = time.monotonic() - self._threshing_start
            self._threshing_sec += elapsed
            self._threshing_start = time.monotonic()

        avgs = self._accum.averages()
        self._storage.set_state("threshing_seconds", str(self._threshing_sec))
        self._storage.update_session(
            self._session_id,
            threshing_min=round(self._threshing_sec / 60, 2),
            unload_count=self._unload_count,
            volume_m3=round(self._volume_m3, 2),
            weight_kg=round(self._weight_kg, 2),
            area_ha=round(self._area_m2 / 10000, 3),
            warn_count=self._warn_count,
            error_count=self._error_count,
            avg_rpm_drum=avgs.get("drum"),
            avg_rpm_kolosa=avgs.get("kolosa"),
            avg_rpm_solomotryas=avgs.get("solomotryas"),
            avg_rpm_fan=avgs.get("fan_speed"),
        )

    # ── Жатка / площадь ───────────────────────────────────────────────────

    def set_header_width(self, width_m: float):
        self._header_width_m = width_m

    # ── Culture ───────────────────────────────────────────────────────────

    def _flush_culture(self, time_end: Optional[datetime] = None):
        if self._session_id is None or not self._culture_start:
            return
        if self._culture_unloads == 0 and self._culture_area_m2 == 0.0:
            return
        self._storage.upsert_culture(
            self._session_id,
            self._culture,
            self._culture_unloads,
            self._culture_volume,
            self._culture_weight,
            self._culture_start,
            time_end,
            area_ha=round(self._culture_area_m2 / 10000, 3),
        )

    def set_culture(self, culture: str):
        if culture == self._culture:
            return
        now = datetime.now()
        self._flush_culture(time_end=now)
        self._culture = culture
        self._culture_start = now
        self._culture_unloads = 0
        self._culture_volume = 0.0
        self._culture_weight = 0.0
        self._culture_area_m2 = 0.0
        if self._session_id is not None:
            self._storage.set_state("current_culture", culture)

    # ── Slots ─────────────────────────────────────────────────────────────

    @pyqtSlot(dict)
    def on_sensor_update(self, readings: dict):
        if not readings:
            return

        drum = readings.get("drum")
        drum_rpm = drum.value if drum else 0.0
        is_threshing = drum_rpm > self._drum_threshold

        # Engine detection (drum as proxy until real engine sensor)
        if is_threshing and not self._engine_running:
            self._on_engine_started()
        elif not is_threshing and self._engine_running:
            self._on_engine_stopped()

        # Threshing time + RPM accumulation
        if is_threshing:
            if self._threshing_start is None:
                self._threshing_start = time.monotonic()
            for name, reading in readings.items():
                if name in _IMPULSE_SENSORS:
                    self._accum.add(name, reading.value)
        else:
            if self._threshing_start is not None:
                self._threshing_sec += time.monotonic() - self._threshing_start
                self._threshing_start = None

        # Area: distance traveled (speed sensor) × header width, only while threshing
        now_mono = time.monotonic()
        speed_reading = readings.get("speed")
        speed_kmh = speed_reading.value if speed_reading else 0.0
        if is_threshing and self._last_speed_mono is not None:
            dt = now_mono - self._last_speed_mono
            if 0 < dt < 5:
                area_m2 = (speed_kmh * 1000.0 / 3600.0 * dt) * self._header_width_m
                self._area_m2 += area_m2
                self._culture_area_m2 += area_m2
        self._last_speed_mono = now_mono

        # Error transitions
        if self._session_id is not None:
            for name, reading in readings.items():
                prev = self._prev_statuses.get(name)
                curr = reading.status
                if prev != curr and curr != SensorStatus.OK:
                    self._log_error_transition(name, reading, curr)
                self._prev_statuses[name] = curr

    def _log_error_transition(self, name: str, reading, status: SensorStatus):
        error_type = "error" if status == SensorStatus.CRITICAL else "warn"
        sensor_cfg = self._config.sensors.get("list", {}).get(name, {})
        if status == SensorStatus.CRITICAL:
            threshold = sensor_cfg.get("error_threshold_low")
        elif status == SensorStatus.WARN_HIGH:
            threshold = sensor_cfg.get("warn_high")
        else:
            threshold = sensor_cfg.get("warn_low")

        self._storage.log_error_event(
            self._session_id, name, error_type, reading.value, threshold
        )
        if error_type == "warn":
            self._warn_count += 1
        else:
            self._error_count += 1

    @pyqtSlot(int)
    def on_unload(self, _count: int):
        if self._session_id is None:
            return
        density = self._densities.get(self._culture, 0.7)
        volume = self._bin_volume
        weight = volume * density * 1000  # kg

        self._unload_count += 1
        self._volume_m3 += volume
        self._weight_kg += weight
        self._culture_unloads += 1
        self._culture_volume += volume
        self._culture_weight += weight

        # Immediate write for unload events
        self._flush_culture()
        self._storage.update_session(
            self._session_id,
            unload_count=self._unload_count,
            volume_m3=round(self._volume_m3, 2),
            weight_kg=round(self._weight_kg, 2),
        )

    def shutdown(self):
        if self._session_id is not None:
            self._close_session()
        self._storage.close()

    # ── Live data for UI ──────────────────────────────────────────────────

    def get_live_session_data(self) -> dict:
        if self._session_id is None:
            return {}
        now_mono = time.monotonic()
        threshing_sec = self._threshing_sec
        if self._threshing_start is not None:
            threshing_sec += now_mono - self._threshing_start

        dur_sec = (
            (datetime.now() - self._session_start).total_seconds()
            if self._session_start else 0.0
        )
        threshing_min = threshing_sec / 60
        dur_min = dur_sec / 60
        eff = (threshing_min / dur_min * 100) if dur_min > 0 else 0.0

        avgs = self._accum.averages()
        return {
            "session_id": self._session_id,
            "start_time": self._session_start,
            "duration_min": dur_min,
            "threshing_min": threshing_min,
            "idle_min": dur_min - threshing_min,
            "efficiency_pct": round(eff, 1),
            "unload_count": self._unload_count,
            "volume_m3": round(self._volume_m3, 2),
            "weight_kg": round(self._weight_kg, 2),
            "area_ha": round(self._area_m2 / 10000, 3),
            "warn_count": self._warn_count,
            "error_count": self._error_count,
            "culture": self._culture,
            "avg_rpm_drum": avgs.get("drum"),
            "avg_rpm_kolosa": avgs.get("kolosa"),
            "avg_rpm_solomotryas": avgs.get("solomotryas"),
            "avg_rpm_fan": avgs.get("fan_speed"),
            "status": "active",
        }

    @property
    def session_id(self) -> Optional[int]:
        return self._session_id

    @property
    def storage(self) -> StatisticsStorage:
        return self._storage
