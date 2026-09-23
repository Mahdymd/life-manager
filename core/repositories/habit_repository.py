"""core/repositories/habit_repository.py"""

from typing import List, Optional, Dict
from datetime import date, timedelta
from core.repositories.base_repository import BaseRepository
from core.domain.models import Habit, HabitLog
from core.domain.enums import HabitFrequency


class HabitRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("habits")

    def _row_to_habit(self, row) -> Habit:
        d = self._row_to_dict(row)
        return Habit(
            id=d["id"], name=d["name"], description=d.get("description"),
            goal_id=d.get("goal_id"), category=d.get("category"),
            frequency=HabitFrequency(d.get("frequency","daily")),
            target_days=d.get("target_days"), target_count=d.get("target_count",1),
            color=d.get("color","#22c55e"), icon=d.get("icon","⭐"),
            archived=bool(d.get("archived",0)), sort_order=d.get("sort_order",0),
            created_at=d["created_at"], updated_at=d["updated_at"],
        )

    def get_all(self, include_archived: bool = False) -> List[Habit]:
        where = "" if include_archived else "WHERE archived=0"
        rows = self._fetch_all(
            f"SELECT * FROM habits {where} ORDER BY sort_order, created_at")
        return [self._row_to_habit(r) for r in rows]

    def get_by_id(self, id_: int) -> Optional[Habit]:
        row = self._fetch_one("SELECT * FROM habits WHERE id=?", (id_,))
        return self._row_to_habit(row) if row else None

    def create(self, name: str, **kwargs) -> Habit:
        id_ = self._insert({"name": name, **kwargs})
        return self.get_by_id(id_)

    def update(self, id_: int, **kwargs) -> bool:
        return self._update(id_, kwargs)

    def log_today(self, habit_id: int, note: str = None) -> bool:
        today = date.today().isoformat()
        now = self._now()
        try:
            self._conn().execute("""
                INSERT INTO habit_logs(habit_id,date,count,note,created_at)
                VALUES(?,?,1,?,?)
                ON CONFLICT(habit_id,date) DO UPDATE SET count=count+1, note=?""",
                (habit_id, today, note, now, note))
            from core.database.connection import commit
            commit()
            return True
        except Exception:
            return False

    def unlog_today(self, habit_id: int) -> bool:
        today = date.today().isoformat()
        cur = self._conn().execute(
            "DELETE FROM habit_logs WHERE habit_id=? AND date=?", (habit_id, today))
        from core.database.connection import commit
        commit()
        return cur.rowcount > 0

    def is_logged(self, habit_id: int, for_date: str = None) -> bool:
        if not for_date:
            for_date = date.today().isoformat()
        row = self._fetch_one(
            "SELECT 1 FROM habit_logs WHERE habit_id=? AND date=?", (habit_id, for_date))
        return row is not None

    def get_logs(self, habit_id: int, from_date: str, to_date: str) -> List[str]:
        rows = self._fetch_all("""
            SELECT date FROM habit_logs
            WHERE habit_id=? AND date BETWEEN ? AND ?
            ORDER BY date""", (habit_id, from_date, to_date))
        return [r["date"] for r in rows]

    def get_streak(self, habit_id: int) -> int:
        today = date.today()
        streak = 0
        current = today
        while True:
            ds = current.isoformat()
            if self.is_logged(habit_id, ds):
                streak += 1
                current -= timedelta(days=1)
            else:
                break
        return streak

    def get_heatmap_data(self, habit_id: int, year: int) -> Dict[str, int]:
        rows = self._fetch_all("""
            SELECT date, count FROM habit_logs
            WHERE habit_id=? AND date LIKE ?
            ORDER BY date""", (habit_id, f"{year}%"))
        return {r["date"]: r["count"] for r in rows}

    def get_heatmap_range(self, habit_id: int, from_date: str, to_date: str) -> Dict[str, int]:
        """مثل get_heatmap_data ولی برای یک بازه‌ی دلخواه (نه کل سال) —
        برای نمایش heatmap فشرده‌ی ۱۲ هفته‌ای در کارت هر عادت (Phase 5)."""
        rows = self._fetch_all("""
            SELECT date, count FROM habit_logs
            WHERE habit_id=? AND date BETWEEN ? AND ?
            ORDER BY date""", (habit_id, from_date, to_date))
        return {r["date"]: r["count"] for r in rows}
