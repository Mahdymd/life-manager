"""
ui/viewmodels/analytics_viewmodel.py

ViewModel صفحه‌ی آنالیتیکس. الگو از task_list_viewmodel.py.

نکته: چون این صفحه از ۷ منبع داده‌ی مستقل تشکیل شده (خلاصه هفته، روند
تسک، روند مالی، آمار عادت، روند سلامت، روند خلق‌وخو، پیشرفت اهداف)،
هر بخش یک تابع worker مستقل و یک سیگنال مستقل دارد — همه به‌صورت
موازی (نه ترتیبی) روی Worker های جدا اجرا می‌شوند تا کندترین بخش
(مثلاً یک کوئری روی جدول تسک‌ها) بقیه‌ی داشبورد را معطل نکند.

هر تابع fetch دقیقاً همان منطق قبلی View را حفظ کرده (فقط از رندر UI
جدا شده) تا رفتار قبلی بدون تغییر باقی بماند.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel


def _fetch_insights() -> List[str]:
    from core.services.analytics_service import generate_insights
    return generate_insights()


def _fetch_weekly_summary() -> Dict:
    from core.services.analytics_service import get_weekly_report
    from core.services.focus_service import get_focus_stats
    from core.services.finance_service import get_summary
    from core.services.habit_service import get_habit_stats

    result: Dict = {"tasks_done": 0, "habit_pct": None, "focus_min": 0, "balance": 0}
    try:
        week = get_weekly_report()
        result["tasks_done"] = week.get("tasks_done", 0)
    except Exception:
        pass
    try:
        h_stats = get_habit_stats()
        total, done = h_stats.get("total", 0), h_stats.get("done_today", 0)
        result["habit_pct"] = int(done / total * 100) if total else None
    except Exception:
        pass
    try:
        f_stats = get_focus_stats()
        result["focus_min"] = f_stats.get("today_focus_min") or 0
    except Exception:
        pass
    try:
        month = date.today().isoformat()[:7]
        summary = get_summary(month)
        result["balance"] = summary.get("balance", 0)
    except Exception:
        pass
    return result


def _fetch_task_trend() -> Optional[Tuple[List[int], List[str]]]:
    try:
        from core.services.task_service import get_completion_trend
        rows = get_completion_trend(6)
        if not rows:
            return None
        vals = [r["cnt"] for r in rows]
        labels = [r["month"][-2:] + "/" + r["month"][:4][2:] for r in rows]
        return vals, labels
    except Exception:
        return None


def _fetch_finance_trend() -> Optional[Tuple[List[str], List[float], List[float]]]:
    try:
        from core.services.finance_service import get_monthly_trend
        trend = get_monthly_trend(6)
        if not trend:
            return None
        labels = [r["month"][-2:] for r in trend]
        incomes = [r.get("income", 0) / 1_000_000 for r in trend]
        expenses = [r.get("expense", 0) / 1_000_000 for r in trend]
        return labels, incomes, expenses
    except Exception:
        return None


def _fetch_habit_stats() -> List[Dict]:
    try:
        from core.services import habit_service
        from core.repositories.habit_repository import HabitRepository
        # Service for list; repository only for streak/logs already used by service internals.
        # Prefer service API for the public list.
        habits = habit_service.get_all_habits()
        repo = HabitRepository()
        today = date.today()
        from_date = (today - timedelta(days=29)).isoformat()
        to_date = today.isoformat()

        result = []
        for habit in habits[:8]:
            logs = repo.get_logs(habit.id, from_date, to_date)
            rate = int(len(logs) / 30 * 100)
            streak = repo.get_streak(habit.id)
            result.append({"habit": habit, "rate": rate, "streak": streak})
        return result
    except Exception:
        return []


def _fetch_health_trend() -> Optional[Tuple[List[float], List[str]]]:
    try:
        from core.services.health_service import get_weight_history
        hist = get_weight_history(30)
        if not hist:
            return None
        vals = [h["value"] for h in hist]
        labels = [h["date"][-5:] for h in hist]
        return vals, labels
    except Exception:
        return None


def _fetch_mood_trend() -> Optional[Tuple[List[int], List[str]]]:
    try:
        from core.services.journal_service import get_mood_data
        today = date.today()
        from_d = (today - timedelta(days=29)).isoformat()
        data = get_mood_data(from_d, today.isoformat())
        if not data:
            return None
        vals = [d.get("mood", 0) or 0 for d in data[-20:]]
        labels = [d["date"][-5:] for d in data[-20:]]
        return vals, labels
    except Exception:
        return None


def _fetch_goal_progress() -> List:
    try:
        from core.services.goal_service import get_all_goals
        return get_all_goals(status="active")[:8]
    except Exception:
        return []


class AnalyticsViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی آنالیتیکس.

    Signals (هر بخش داشبورد یک سیگنال مستقل — تا هرکدام به‌محض آماده
    شدن، بدون منتظر ماندن برای بقیه، رندر شود):
        weekly_summary_loaded(dict)
        task_trend_loaded(object): (values, labels) یا None
        finance_trend_loaded(object): (labels, incomes, expenses) یا None
        habit_stats_loaded(list[dict])
        health_trend_loaded(object): (values, labels) یا None
        mood_trend_loaded(object): (values, labels) یا None
        goal_progress_loaded(list[Goal])
    """

    weekly_summary_loaded = Signal(dict)
    task_trend_loaded = Signal(object)
    finance_trend_loaded = Signal(object)
    habit_stats_loaded = Signal(list)
    health_trend_loaded = Signal(object)
    mood_trend_loaded = Signal(object)
    goal_progress_loaded = Signal(list)
    insights_loaded = Signal(list)

    def load(self) -> None:
        """همه‌ی ۸ بخش را موازی (نه ترتیبی) بارگذاری می‌کند."""
        self.run_async(_fetch_weekly_summary, self.weekly_summary_loaded.emit)
        self.run_async(_fetch_task_trend, self.task_trend_loaded.emit)
        self.run_async(_fetch_finance_trend, self.finance_trend_loaded.emit)
        self.run_async(_fetch_habit_stats, self.habit_stats_loaded.emit)
        self.run_async(_fetch_health_trend, self.health_trend_loaded.emit)
        self.run_async(_fetch_mood_trend, self.mood_trend_loaded.emit)
        self.run_async(_fetch_goal_progress, self.goal_progress_loaded.emit)
        self.run_async(_fetch_insights, self.insights_loaded.emit)
