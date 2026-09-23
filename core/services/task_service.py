"""core/services/task_service.py — Business logic تسک‌ها."""

import json, logging
from datetime import date, timedelta
from typing import List, Optional, Dict
from core.repositories.task_repository import TaskRepository
from core.domain.models import Task
from core.domain.enums import TaskStatus, TaskRecurrence
from core.domain.exceptions import RequiredFieldError, BusinessRuleError
from utils.validator import require

logger = logging.getLogger("life_manager.task_service")
_repo = TaskRepository()


def create_task(title: str, **kwargs) -> Task:
    title = require(title, "عنوان تسک")
    return _repo.create(title, **kwargs)


def update_task(id_: int, **kwargs) -> bool:
    if "title" in kwargs:
        kwargs["title"] = require(kwargs["title"], "عنوان تسک")
    return _repo.update(id_, **kwargs)


def complete_task(id_: int) -> bool:
    from core.database.connection import transaction
    task = _repo.get_by_id(id_)
    if not task:
        raise BusinessRuleError("تسک پیدا نشد.")
    with transaction():
        result = _repo.complete(id_)
        if result and task.recurrence != TaskRecurrence.NONE:
            _spawn_next_recurrence(task)
    return result


def _spawn_next_recurrence(task: Task) -> None:
    """ایجاد نسخه بعدی تسک تکراری."""
    try:
        if not task.due_date:
            return
        current = date.fromisoformat(task.due_date)
        if task.recurrence == TaskRecurrence.DAILY:
            next_date = current + timedelta(days=1)
        elif task.recurrence == TaskRecurrence.WEEKLY:
            next_date = current + timedelta(weeks=1)
        elif task.recurrence == TaskRecurrence.MONTHLY:
            m = current.month + 1
            y = current.year + (m - 1) // 12
            m = (m - 1) % 12 + 1
            d = min(current.day, [31,28+int(y%4==0 and (y%100!=0 or y%400==0)),
                                   31,30,31,30,31,31,30,31,30,31][m-1])
            next_date = date(y, m, d)
        else:
            return
        _repo.create(
            task.title,
            description=task.description,
            project_id=task.project_id,
            goal_id=task.goal_id,
            category_id=task.category_id,
            due_date=next_date.isoformat(),
            priority=task.priority.value,
            recurrence=task.recurrence.value,
            recur_config=task.recur_config,
        )
    except Exception as e:
        logger.error("Failed to spawn recurrence: %s", e)


def delete_task(id_: int) -> bool:
    return _repo.delete(id_)


def get_task(id_: int) -> Optional[Task]:
    return _repo.get_by_id(id_)


def get_all_tasks(**kwargs) -> List[Task]:
    return _repo.get_all(**kwargs)


def get_today_tasks() -> List[Task]:
    return _repo.get_today()


def get_overdue_tasks() -> List[Task]:
    return _repo.get_overdue()


def get_task_stats() -> Dict:
    return _repo.get_stats()


def get_subtasks(parent_id: int) -> List[Task]:
    return _repo.get_subtasks(parent_id)


def get_completion_trend(months: int = 6) -> List[Dict]:
    """Monthly completed-task counts for analytics charts.
    Returns list of {month: 'YYYY-MM', cnt: int}, oldest first.
    """
    from core.database.connection import get_connection
    rows = get_connection().execute(
        """
        SELECT strftime('%Y-%m', completed_at) AS month, COUNT(*) AS cnt
        FROM tasks WHERE status='done' AND completed_at IS NOT NULL
        GROUP BY month ORDER BY month DESC LIMIT ?
        """,
        (months,),
    ).fetchall()
    return [{"month": r["month"], "cnt": r["cnt"]} for r in reversed(list(rows))]
