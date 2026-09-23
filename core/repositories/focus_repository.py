"""core/repositories/focus_repository.py"""

from typing import List, Dict
from datetime import date
from core.repositories.base_repository import BaseRepository
from core.domain.models import FocusSession
from core.domain.enums import FocusSessionType, FocusSessionStatus


class FocusRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("focus_sessions")

    def _to_session(self, row) -> FocusSession:
        d = self._row_to_dict(row)
        return FocusSession(
            id=d["id"], task_id=d.get("task_id"),
            type=FocusSessionType(d.get("type","pomodoro")),
            planned_min=d["planned_min"], actual_min=d.get("actual_min"),
            status=FocusSessionStatus(d.get("status","completed")),
            started_at=d["started_at"], ended_at=d.get("ended_at"),
            note=d.get("note"), created_at=d["created_at"],
        )

    def add(self, type_: str, planned_min: int, started_at: str, **kwargs) -> FocusSession:
        id_ = self._insert({"type": type_, "planned_min": planned_min,
                            "started_at": started_at, **kwargs})
        row = self._fetch_one("SELECT * FROM focus_sessions WHERE id=?", (id_,))
        return self._to_session(row)

    def update(self, id_: int, **kwargs) -> bool:
        return self._update(id_, kwargs)

    def get_today_sessions(self) -> List[FocusSession]:
        today = date.today().isoformat()
        rows = self._fetch_all("""
            SELECT * FROM focus_sessions WHERE started_at LIKE ?
            ORDER BY started_at""", (f"{today}%",))
        return [self._to_session(r) for r in rows]

    def get_stats(self) -> Dict:
        today = date.today().isoformat()
        row = self._fetch_one("""
            SELECT
              SUM(CASE WHEN started_at LIKE ? AND type='pomodoro' AND status='completed'
                  THEN 1 ELSE 0 END) AS today_pomodoros,
              SUM(CASE WHEN started_at LIKE ? AND type='pomodoro' AND status='completed'
                  THEN actual_min ELSE 0 END) AS today_focus_min,
              COUNT(CASE WHEN type='pomodoro' AND status='completed' THEN 1 END) AS total_pomodoros
            FROM focus_sessions""", (f"{today}%", f"{today}%"))
        return dict(row) if row else {}
