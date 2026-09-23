"""core/services/analytics_service.py — Analytics چند ماژولی."""

from datetime import date, timedelta
from typing import Dict, List
from core.repositories.task_repository import TaskRepository
from core.repositories.habit_repository import HabitRepository
from core.repositories.finance_repository import FinanceRepository
from core.repositories.focus_repository import FocusRepository
from core.repositories.journal_repository import JournalRepository

_task = TaskRepository()
_habit = HabitRepository()
_finance = FinanceRepository()
_focus = FocusRepository()
_journal = JournalRepository()


def get_dashboard_summary() -> Dict:
    today = date.today().isoformat()
    month = today[:7]
    task_stats = _task.get_stats()
    finance_summary = _finance.get_summary(month)
    focus_stats = _focus.get_stats()
    today_journal = _journal.get_by_date(today)
    habits = _habit.get_all(include_archived=False)
    habits_today = sum(1 for h in habits if _habit.is_logged(h.id, today))
    return {
        "tasks": task_stats,
        "finance": finance_summary,
        "focus": focus_stats,
        "habits": {"total": len(habits), "done_today": habits_today},
        "journal": {"has_entry": today_journal is not None,
                    "mood": today_journal.mood if today_journal else None},
    }


def get_weekly_report(weeks_back: int = 0) -> Dict:
    today = date.today()
    start = today - timedelta(days=today.weekday() + weeks_back * 7)
    end = start + timedelta(days=6)
    s, e = start.isoformat(), end.isoformat()
    tasks_done = _task._fetch_one("""
        SELECT COUNT(*) AS cnt FROM tasks
        WHERE status='done' AND completed_at BETWEEN ? AND ?""", (s, e+" 23:59:59"))
    finance = _finance._fetch_one("""
        SELECT SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc,
               SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
        FROM transactions WHERE date BETWEEN ? AND ?""", (s, e))
    return {
        "period": f"{s} تا {e}",
        "tasks_done": tasks_done["cnt"] if tasks_done else 0,
        "income": finance["inc"] or 0 if finance else 0,
        "expense": finance["exp"] or 0 if finance else 0,
    }


_WEEKDAY_FA_BY_SQLITE_DOW = ["یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه",
                             "پنجشنبه", "جمعه", "شنبه"]


def generate_insights() -> List[Dict[str, str]]:
    """کارت‌های بینش هیوریستیک — طبق بخش ۶ اسپک: "Analytics Insights:
    heuristic‑driven cards (\"Saturdays are your most productive days\")".

    هر آیتم دیکشنری {"icon": ..., "text": ...} است؛ نام آیکون از
    ui/style/icons.py می‌آید (نه ایموجی) و انتخاب آن اینجا صرفاً برای
    مشخص‌کردن «نوع» insight است، نه فرمت‌دهی بصری — رندر واقعی در
    ui/pages/analytics_page.py انجام می‌شود.

    هر بخش مستقل try/except دارد تا نبود داده در یک ماژول (مثلاً هیچ
    تسک انجام‌شده‌ای) باعث نشود کل تابع خطا بدهد و بقیه‌ی insight ها
    از دست بروند.
    """
    insights: List[Dict[str, str]] = []

    # ۱. پرکارترین روز هفته (بر اساس تسک‌های انجام‌شده)
    try:
        rows = _task._fetch_all("""
            SELECT strftime('%w', completed_at) AS dow, COUNT(*) AS cnt
            FROM tasks WHERE status='done' AND completed_at IS NOT NULL
            GROUP BY dow ORDER BY cnt DESC LIMIT 1""")
        if rows and rows[0]["cnt"] >= 3:
            dow_idx = int(rows[0]["dow"])
            insights.append({"icon": "calendar", "text":
                f"{_WEEKDAY_FA_BY_SQLITE_DOW[dow_idx]}‌ها پرکارترین روز شماست "
                f"({rows[0]['cnt']} تسک انجام‌شده تا امروز)."})
    except Exception:
        pass

    # ۲. روند تکمیل عادت‌ها: این هفته در مقابل هفته‌ی قبل
    try:
        today = date.today()
        this_week_start = (today - timedelta(days=today.weekday())).isoformat()
        last_week_start = (today - timedelta(days=today.weekday() + 7)).isoformat()
        last_week_end = (today - timedelta(days=today.weekday() + 1)).isoformat()

        this_week_logs = _habit._fetch_one(
            "SELECT COUNT(*) AS cnt FROM habit_logs WHERE date >= ?", (this_week_start,))
        last_week_logs = _habit._fetch_one(
            "SELECT COUNT(*) AS cnt FROM habit_logs WHERE date BETWEEN ? AND ?",
            (last_week_start, last_week_end))
        this_cnt = this_week_logs["cnt"] if this_week_logs else 0
        last_cnt = last_week_logs["cnt"] if last_week_logs else 0
        if last_cnt > 0:
            if this_cnt > last_cnt:
                insights.append({"icon": "flame", "text":
                    f"این هفته {this_cnt} بار عادت ثبت کردی، بهتر از هفته‌ی قبل ({last_cnt} بار)."})
            elif this_cnt < last_cnt:
                insights.append({"icon": "warning", "text":
                    f"این هفته فقط {this_cnt} بار عادت ثبت کردی، کمتر از هفته‌ی قبل ({last_cnt} بار)."})
    except Exception:
        pass

    # ۳. میانگین حال‌وهوا این ماه در مقابل ماه قبل
    try:
        this_month = date.today().isoformat()[:7]
        last_month_date = (date.today().replace(day=1) - timedelta(days=1))
        last_month = last_month_date.isoformat()[:7]

        this_mood = _journal._fetch_one(
            "SELECT AVG(mood) AS avg_mood FROM journal_entries WHERE date LIKE ? AND mood IS NOT NULL",
            (f"{this_month}%",))
        last_mood = _journal._fetch_one(
            "SELECT AVG(mood) AS avg_mood FROM journal_entries WHERE date LIKE ? AND mood IS NOT NULL",
            (f"{last_month}%",))
        this_avg = this_mood["avg_mood"] if this_mood and this_mood["avg_mood"] else None
        last_avg = last_mood["avg_mood"] if last_mood and last_mood["avg_mood"] else None
        if this_avg is not None and last_avg is not None:
            diff = this_avg - last_avg
            if diff >= 0.4:
                insights.append({"icon": "smile", "text":
                    f"حال‌وهوای این ماهت نسبت به ماه قبل بهتر شده ({this_avg:.1f} در مقابل {last_avg:.1f})."})
            elif diff <= -0.4:
                insights.append({"icon": "trending_down", "text":
                    f"حال‌وهوای این ماهت نسبت به ماه قبل افت کرده ({this_avg:.1f} در مقابل {last_avg:.1f})."})
    except Exception:
        pass

    # ۴. بیشترین دسته‌بندی هزینه‌ی این ماه
    try:
        this_month = date.today().isoformat()[:7]
        top_category = _finance._fetch_one("""
            SELECT c.name, SUM(t.amount) AS total
            FROM transactions t LEFT JOIN categories c ON c.id = t.category_id
            WHERE t.type='expense' AND t.date LIKE ?
            GROUP BY t.category_id ORDER BY total DESC LIMIT 1""", (f"{this_month}%",))
        if top_category and top_category["total"]:
            from utils.number_utils import format_currency
            name = top_category["name"] or "متفرقه"
            insights.append({"icon": "money", "text":
                f"بیشترین هزینه‌ی این ماهت مربوط به «{name}» بوده ({format_currency(top_category['total'])})."})
    except Exception:
        pass

    return insights
