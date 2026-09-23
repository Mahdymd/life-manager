"""core/repositories/calendar_repository.py"""

from typing import List
from core.repositories.base_repository import BaseRepository
from core.domain.models import CalendarEvent
from core.domain.enums import EventType


class CalendarRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("events")

    def _to_event(self, row) -> CalendarEvent:
        d = self._row_to_dict(row)
        return CalendarEvent(
            id=d["id"], title=d["title"], description=d.get("description"),
            date=d["date"], time=d.get("time"), end_date=d.get("end_date"),
            end_time=d.get("end_time"), is_all_day=bool(d.get("is_all_day",1)),
            type=EventType(d.get("type","personal")),
            recurrence=d.get("recurrence","none"),
            recur_config=d.get("recur_config"), color=d.get("color","#6366f1"),
            created_at=d["created_at"], updated_at=d["updated_at"],
        )

    def get_by_month(self, year: int, month: int) -> List[CalendarEvent]:
        month_str = f"{year}-{month:02d}"
        rows = self._fetch_all("""
            SELECT * FROM events WHERE date LIKE ?
            ORDER BY date, time""", (f"{month_str}%",))
        return [self._to_event(r) for r in rows]

    def get_by_date(self, date: str) -> List[CalendarEvent]:
        rows = self._fetch_all(
            "SELECT * FROM events WHERE date=? ORDER BY time", (date,))
        return [self._to_event(r) for r in rows]

    def add(self, title: str, date: str, **kwargs) -> CalendarEvent:
        id_ = self._insert({"title": title, "date": date, **kwargs})
        row = self._fetch_one("SELECT * FROM events WHERE id=?", (id_,))
        return self._to_event(row)

    def update(self, id_: int, **kwargs) -> bool:
        return self._update(id_, kwargs)
