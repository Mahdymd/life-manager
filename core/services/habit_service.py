"""core/services/habit_service.py — Business logic عادت‌ها."""

from typing import List, Optional, Dict
from datetime import date
from core.repositories.habit_repository import HabitRepository
from core.domain.models import Habit
from utils.validator import require

_repo = HabitRepository()


def create_habit(name: str, **kwargs) -> Habit:
    name = require(name, "نام عادت")
    return _repo.create(name, **kwargs)


def update_habit(id_: int, **kwargs) -> bool:
    return _repo.update(id_, **kwargs)


def delete_habit(id_: int) -> bool:
    return _repo.delete(id_)


def archive_habit(id_: int) -> bool:
    return _repo.update(id_, archived=1)


def get_all_habits(include_archived: bool = False) -> List[Habit]:
    habits = _repo.get_all(include_archived)
    for h in habits:
        h.logged_today = _repo.is_logged(h.id)
        h.current_streak = _repo.get_streak(h.id)
    return habits


def toggle_today(habit_id: int) -> bool:
    """toggle وضعیت عادت امروز."""
    if _repo.is_logged(habit_id):
        return _repo.unlog_today(habit_id)
    else:
        return _repo.log_today(habit_id)


def get_heatmap(habit_id: int, year: int = None) -> Dict[str, int]:
    if year is None:
        year = date.today().year
    return _repo.get_heatmap_data(habit_id, year)


def get_heatmap_range(habit_id: int, from_date: str, to_date: str) -> Dict[str, int]:
    """heatmap فشرده برای یک بازه‌ی دلخواه (مثلاً ۱۲ هفته‌ی اخیر برای
    کارت هر عادت) — طبق بخش ۴ اسپک: "GitHub‑style heatmap"."""
    return _repo.get_heatmap_range(habit_id, from_date, to_date)


def get_habit_stats() -> Dict:
    habits = _repo.get_all(include_archived=False)
    total = len(habits)
    today = date.today().isoformat()
    done_today = sum(1 for h in habits if _repo.is_logged(h.id, today))
    return {"total": total, "done_today": done_today, "pending": total - done_today}
