"""
ui/viewmodels/habit_list_viewmodel.py

ViewModel صفحه‌ی عادت‌ها. الگوی این فایل مستقیماً از
task_list_viewmodel.py (نمونه‌ی مرجع Phase 3) کپی شده است.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, List
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.domain.models import Habit
from core.services.habit_service import (
    get_all_habits,
    get_habit_stats,
    get_heatmap_range,
    create_habit,
    update_habit,
    delete_habit,
    toggle_today,
)

_HEATMAP_WEEKS = 12
_NUDGE_THRESHOLD_DAYS = 3
_MILESTONE_STREAKS = {7, 14, 21, 30, 50, 100, 200, 365}


def _fetch_heatmaps(habit_ids: List[int]) -> Dict[int, Dict]:
    """در worker thread اجرا می‌شود. برای هر عادت، هم داده‌ی heatmap
    (۱۲ هفته‌ی اخیر) و هم تعداد روزهای متوالی ازدست‌رفته (قبل از امروز،
    نه شامل امروز — چون امروز هنوز تمام نشده) را برمی‌گرداند.
    """
    today = date.today()
    from_date = (today - timedelta(weeks=_HEATMAP_WEEKS)).isoformat()
    to_date = today.isoformat()

    result: Dict[int, Dict] = {}
    for hid in habit_ids:
        data = get_heatmap_range(hid, from_date, to_date)
        missed = 0
        d = today - timedelta(days=1)
        while missed < 60 and (d.isoformat() not in data or data[d.isoformat()] <= 0):
            missed += 1
            d -= timedelta(days=1)
        result[hid] = {"heatmap": data, "missed_days": missed}
    return result


class HabitListViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی عادت‌ها.

    Signals:
        habits_changed(list[Habit])
        stats_changed(dict)
        heatmaps_changed(dict): {habit_id: {"heatmap": {date:count}, "missed_days": int}}
        nudge_needed(object): یک Habit که ۳+ روز متوالی ازدست‌رفته (طبق
            بخش ۴ اسپک: "Smart nudge if missed 3 days").
    """

    habits_changed = Signal(list)
    stats_changed = Signal(dict)
    heatmaps_changed = Signal(dict)
    nudge_needed = Signal(object)
    streak_milestone_reached = Signal(object)  # Habit با streak جدید که به یک نقطه‌ی عطف رسیده

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._habits: List[Habit] = []
        self._stats: Dict = {}
        # از تکرار nudge برای یک عادت در طول یک session جلوگیری می‌کند
        self._nudged_habit_ids: set = set()
        # (habit_id, streak_قبل_از_toggle) — برای تشخیص عبور از نقطه‌ی
        # عطف بعد از بارگذاری async لیست جدید
        self._pending_milestone_check: tuple = None

    @property
    def habits(self) -> List[Habit]:
        return self._habits

    @property
    def stats(self) -> Dict:
        return self._stats

    def load(self) -> None:
        self.run_async(get_habit_stats, self._on_stats_loaded)
        self.run_async(get_all_habits, self._on_habits_loaded)

    def _on_stats_loaded(self, stats: Dict) -> None:
        self._stats = stats
        self.stats_changed.emit(stats)

    def _on_habits_loaded(self, habits: List[Habit]) -> None:
        self._habits = habits
        self.habits_changed.emit(habits)
        if habits:
            habit_ids = [h.id for h in habits]
            self.run_async(_fetch_heatmaps, self._on_heatmaps_loaded, habit_ids)
        self._check_pending_milestone()

    def _check_pending_milestone(self) -> None:
        if not self._pending_milestone_check:
            return
        habit_id, old_streak = self._pending_milestone_check
        self._pending_milestone_check = None
        habit = next((h for h in self._habits if h.id == habit_id), None)
        if (habit and habit.current_streak > old_streak
                and habit.current_streak in _MILESTONE_STREAKS):
            self.streak_milestone_reached.emit(habit)

    def _on_heatmaps_loaded(self, heatmaps: Dict[int, Dict]) -> None:
        self.heatmaps_changed.emit(heatmaps)
        by_id = {h.id: h for h in self._habits}
        for habit_id, info in heatmaps.items():
            if (info["missed_days"] >= _NUDGE_THRESHOLD_DAYS
                    and habit_id not in self._nudged_habit_ids):
                self._nudged_habit_ids.add(habit_id)
                habit = by_id.get(habit_id)
                if habit:
                    self.nudge_needed.emit(habit)

    def create(self, **data) -> None:
        self.run_async(create_habit, lambda _r: self.load(), **data)

    def update(self, id_: int, **data) -> None:
        self.run_async(update_habit, lambda _r: self.load(), id_, **data)

    def toggle_today(self, id_: int) -> None:
        habit = next((h for h in self._habits if h.id == id_), None)
        old_streak = habit.current_streak if habit else 0
        self._pending_milestone_check = (id_, old_streak)
        self.run_async(toggle_today, lambda _r: self.load(), id_)

    def remove(self, id_: int) -> None:
        self.run_async(delete_habit, lambda _r: self.load(), id_)

