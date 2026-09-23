"""core/services/goal_service.py — Business logic اهداف."""

from typing import List, Optional, Dict
from core.repositories.goal_repository import GoalRepository
from core.repositories.task_repository import TaskRepository
from core.domain.models import Goal, GoalKeyResult
from core.domain.enums import GoalProgressMode
from core.domain.exceptions import BusinessRuleError, CircularDependencyError
from utils.validator import require

_repo = GoalRepository()
_task_repo = TaskRepository()


def create_goal(title: str, horizon: str, **kwargs) -> Goal:
    title = require(title, "عنوان هدف")
    if "parent_goal_id" in kwargs and kwargs["parent_goal_id"]:
        parent = _repo.get_by_id(kwargs["parent_goal_id"])
        if not parent:
            raise BusinessRuleError("هدف والد پیدا نشد.")
    return _repo.create(title, horizon, **kwargs)


def update_goal(id_: int, **kwargs) -> bool:
    if "parent_goal_id" in kwargs and kwargs["parent_goal_id"] == id_:
        raise CircularDependencyError("Goal")
    return _repo.update(id_, **kwargs)


def delete_goal(id_: int) -> bool:
    return _repo.delete(id_)


def get_goal(id_: int) -> Optional[Goal]:
    goal = _repo.get_by_id(id_)
    if goal:
        goal.computed_progress = compute_progress(id_)
    return goal


def get_all_goals(**kwargs) -> List[Goal]:
    goals = _repo.get_all(**kwargs)
    for g in goals:
        g.computed_progress = compute_progress(g.id)
    return goals


def compute_progress(goal_id: int) -> float:
    """محاسبه بازگشتی پیشرفت هدف."""
    goal = _repo.get_by_id(goal_id)
    if not goal:
        return 0.0
    if goal.progress_mode == GoalProgressMode.MANUAL:
        return goal.manual_progress

    # بررسی Key Results
    krs = _repo.get_key_results(goal_id)
    if krs:
        total = sum(kr.target for kr in krs)
        if total == 0:
            return 0.0
        achieved = sum(min(kr.current, kr.target) for kr in krs)
        return round((achieved / total) * 100, 1)

    # بررسی زیراهداف
    children = _repo.get_children(goal_id)
    if children:
        progresses = [compute_progress(c.id) for c in children]
        return round(sum(progresses) / len(progresses), 1)

    # بررسی تسک‌های مرتبط
    tasks = _task_repo.get_all(goal_id=goal_id)
    if tasks:
        done = sum(1 for t in tasks if t.status.value == "done")
        return round((done / len(tasks)) * 100, 1)

    return 0.0


def get_key_results(goal_id: int) -> List[GoalKeyResult]:
    return _repo.get_key_results(goal_id)


def upsert_key_result(goal_id: int, **kwargs) -> int:
    return _repo.upsert_key_result(goal_id, **kwargs)


def delete_key_result(kr_id: int) -> bool:
    return _repo.delete_key_result(kr_id)


def get_goal_stats() -> Dict:
    return _repo.get_stats()


def generate_catchup_plan(goal_id: int) -> Optional[str]:
    """اگر هدف عقب‌تر از برنامه‌ی زمانی‌اش باشد، یک پیشنهاد متنی برای
    جبران عقب‌ماندگی تولید می‌کند؛ در غیر این صورت None (یعنی هدف طبق
    برنامه یا جلوتر است — نیازی به هشدار نیست).

    طبق بخش ۴ اسپک: "Goals: ... catch-up plan generation".
    """
    goal = get_goal(goal_id)
    if not goal or not goal.target_date:
        return None

    from datetime import date
    try:
        start = (date.fromisoformat(goal.start_date) if goal.start_date
                  else date.fromisoformat(goal.created_at[:10]))
        target = date.fromisoformat(goal.target_date)
    except (ValueError, TypeError):
        return None

    today = date.today()
    total_days = (target - start).days
    remaining_days = (target - today).days

    if total_days <= 0 or remaining_days <= 0:
        return None  # بازه‌ی زمانی نامعتبر یا موعد گذشته (پیام جدا در UI)

    elapsed_days = max(0, (today - start).days)
    expected_progress = min(100.0, (elapsed_days / total_days) * 100)
    actual = goal.computed_progress

    gap = expected_progress - actual
    if gap <= 10:
        return None  # طبق برنامه یا جلوتر — نیازی به catch-up plan نیست

    remaining_progress = max(0.0, 100 - actual)
    remaining_weeks = max(1.0, remaining_days / 7)
    weekly_needed = remaining_progress / remaining_weeks

    return (
        f"عقب‌افتاده‌ای — الان {actual:.0f}٪ (انتظار می‌رفت {expected_progress:.0f}٪ باشی). "
        f"برای رسیدن به موعد، باید هفته‌ای حدود {weekly_needed:.0f}٪ پیشرفت کنی."
    )
