"""core/repositories/health_repository.py"""

from typing import List, Dict, Optional
from core.repositories.base_repository import BaseRepository
from core.domain.models import HealthMetric, Workout
from core.domain.enums import HealthMetricType


class HealthRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("health_metrics")

    def upsert_metric(self, date: str, type_: str, value: float, note: str = None) -> None:
        now = self._now()
        self._conn().execute("""
            INSERT INTO health_metrics(date,type,value,note,created_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(date,type) DO UPDATE SET value=?,note=?""",
            (date, type_, value, note, now, value, note))
        from core.database.connection import commit
        commit()

    def get_metric(self, date: str, type_: str) -> Optional[float]:
        row = self._fetch_one(
            "SELECT value FROM health_metrics WHERE date=? AND type=?", (date, type_))
        return row["value"] if row else None

    def get_metric_history(self, type_: str, limit: int = 30) -> List[Dict]:
        rows = self._fetch_all("""
            SELECT date, value FROM health_metrics
            WHERE type=? ORDER BY date DESC LIMIT ?""", (type_, limit))
        return [dict(r) for r in reversed(rows)]

    def get_today_metrics(self, date: str) -> Dict[str, float]:
        rows = self._fetch_all(
            "SELECT type, value FROM health_metrics WHERE date=?", (date,))
        return {r["type"]: r["value"] for r in rows}

    def add_workout(self, date: str, type_: str, **kwargs) -> None:
        now = self._now()
        self._conn().execute("""
            INSERT INTO workouts(date,type,duration_min,calories,note,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?)""",
            (date, type_, kwargs.get("duration_min"), kwargs.get("calories"),
             kwargs.get("note"), now, now))
        from core.database.connection import commit
        commit()

    def get_workouts(self, limit: int = 20) -> List[Dict]:
        rows = self._fetch_all(
            "SELECT * FROM workouts ORDER BY date DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]
