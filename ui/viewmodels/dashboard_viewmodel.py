"""
ui/viewmodels/dashboard_viewmodel.py

ViewModel داشبورد اصلی. الگو از task_list_viewmodel.py.

نکته: این صفحه از ابتدا در لیست «۱۱ صفحه‌ی باقی‌مانده»ی فاز ۳ فراموش شده
بود؛ این فایل آن گپ را می‌بندد و آخرین صفحه‌ی برنامه است که هنوز
مستقیم service صدا می‌زد.
"""

from __future__ import annotations
from typing import Dict, List
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.services.analytics_service import get_dashboard_summary


def _fetch_today_tasks() -> List:
    from core.services.task_service import get_today_tasks
    return get_today_tasks()[:6]


def _fetch_habits() -> List:
    from core.services.habit_service import get_all_habits
    return get_all_habits()[:6]


class DashboardViewModel(BaseViewModel):
    """State و business-orchestration داشبورد اصلی.

    Signals:
        stats_changed(dict): خلاصه‌ی کارت‌های آماری (تسک/عادت/مالی/فوکوس).
        today_tasks_changed(list): تسک‌های امروز (حداکثر ۶ مورد).
        habits_changed(list): عادت‌ها (حداکثر ۶ مورد).
    """

    stats_changed = Signal(dict)
    today_tasks_changed = Signal(list)
    habits_changed = Signal(list)

    def load(self) -> None:
        """هر سه بخش را موازی (نه ترتیبی) بارگذاری می‌کند."""
        self.run_async(get_dashboard_summary, self.stats_changed.emit)
        self.run_async(_fetch_today_tasks, self.today_tasks_changed.emit)
        self.run_async(_fetch_habits, self.habits_changed.emit)
