"""
ui/viewmodels/health_viewmodel.py

ViewModel صفحه‌ی سلامت. الگو از task_list_viewmodel.py.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.services.health_service import (
    get_today,
    get_recent_workouts,
    log_weight,
    log_water,
    log_sleep,
    log_workout,
)


class HealthViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی سلامت.

    Signals:
        today_changed(dict): متریک‌های امروز (وزن/آب/خواب).
        workouts_changed(list[dict]): آخرین تمرینات ثبت‌شده.
    """

    today_changed = Signal(dict)
    workouts_changed = Signal(list)

    def load(self) -> None:
        self.run_async(get_today, self._on_today_loaded)
        self.run_async(get_recent_workouts, self._on_workouts_loaded, 15)

    def _on_today_loaded(self, data: Dict) -> None:
        self.today_changed.emit(data)

    def _on_workouts_loaded(self, workouts: List[Dict]) -> None:
        self.workouts_changed.emit(workouts)

    def log_weight(self, value: float) -> None:
        self.run_async(log_weight, lambda _r: self.load(), value)

    def log_water(self, glasses: int) -> None:
        self.run_async(log_water, lambda _r: self.load(), glasses)

    def log_sleep(self, hours: float, quality: Optional[int] = None) -> None:
        self.run_async(log_sleep, lambda _r: self.load(), hours, quality)

    def log_workout(self, **data) -> None:
        self.run_async(log_workout, lambda _r: self.load(), **data)
