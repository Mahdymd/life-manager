"""core/repositories/task_repository.py"""

from typing import List, Optional, Dict, Any
from datetime import date
from core.repositories.base_repository import BaseRepository
from core.domain.models import Task
from core.domain.enums import TaskStatus, TaskPriority, TaskRecurrence


class TaskRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("tasks")

    def _row_to_task(self, row) -> Task:
        d = self._row_to_dict(row)
        return Task(
            id=d["id"], title=d["title"], description=d.get("description"),
            project_id=d.get("project_id"), goal_id=d.get("goal_id"),
            parent_task_id=d.get("parent_task_id"), category_id=d.get("category_id"),
            due_date=d.get("due_date"), due_time=d.get("due_time"),
            priority=TaskPriority(d.get("priority","medium")),
            status=TaskStatus(d.get("status","todo")),
            estimated_min=d.get("estimated_min"), actual_min=d.get("actual_min"),
            recurrence=TaskRecurrence(d.get("recurrence","none")),
            recur_config=d.get("recur_config"), completed_at=d.get("completed_at"),
            sort_order=d.get("sort_order",0),
            created_at=d["created_at"], updated_at=d["updated_at"],
            category_name=d.get("category_name"),
        )

    def get_by_id(self, id_: int) -> Optional[Task]:
        row = self._fetch_one("""
            SELECT t.*, c.name AS category_name
            FROM tasks t LEFT JOIN categories c ON c.id=t.category_id
            WHERE t.id=?""", (id_,))
        return self._row_to_task(row) if row else None

    def get_all(self, status: Optional[str] = None,
                project_id: Optional[int] = None,
                goal_id: Optional[int] = None,
                parent_task_id: Optional[int] = None,
                due_date: Optional[str] = None,
                search: Optional[str] = None) -> List[Task]:
        wheres, params = ["t.parent_task_id IS NULL"], []
        if parent_task_id is not None:
            wheres = ["t.parent_task_id = ?"]
            params = [parent_task_id]
        else:
            if status:
                wheres.append("t.status=?"); params.append(status)
            if project_id is not None:
                wheres.append("t.project_id=?"); params.append(project_id)
            if goal_id is not None:
                wheres.append("t.goal_id=?"); params.append(goal_id)
            if due_date:
                wheres.append("t.due_date=?"); params.append(due_date)
            if search:
                wheres.append("t.title LIKE ?"); params.append(f"%{search}%")
        where_sql = " AND ".join(wheres)
        rows = self._fetch_all(f"""
            SELECT t.*, c.name AS category_name
            FROM tasks t LEFT JOIN categories c ON c.id=t.category_id
            WHERE {where_sql}
            ORDER BY t.sort_order, t.priority DESC, t.due_date, t.created_at""",
            tuple(params))
        return [self._row_to_task(r) for r in rows]

    def get_today(self) -> List[Task]:
        today = date.today().isoformat()
        rows = self._fetch_all("""
            SELECT t.*, c.name AS category_name
            FROM tasks t LEFT JOIN categories c ON c.id=t.category_id
            WHERE t.due_date=? AND t.status NOT IN ('done','cancelled')
            ORDER BY t.priority DESC, t.sort_order""", (today,))
        return [self._row_to_task(r) for r in rows]

    def get_overdue(self) -> List[Task]:
        today = date.today().isoformat()
        rows = self._fetch_all("""
            SELECT t.*, c.name AS category_name
            FROM tasks t LEFT JOIN categories c ON c.id=t.category_id
            WHERE t.due_date < ? AND t.status NOT IN ('done','cancelled')
            ORDER BY t.due_date, t.priority DESC""", (today,))
        return [self._row_to_task(r) for r in rows]

    def create(self, title: str, **kwargs) -> Task:
        data: Dict[str, Any] = {"title": title, **kwargs}
        id_ = self._insert(data)
        return self.get_by_id(id_)

    def update(self, id_: int, **kwargs) -> bool:
        self._snapshot_history("task", id_, "update")
        return self._update(id_, kwargs)

    def complete(self, id_: int) -> bool:
        from utils.date_utils import now_iso
        self._snapshot_history("task", id_, "update")
        return self._update(id_, {"status": "done", "completed_at": now_iso()})

    def delete(self, id_: int) -> bool:
        self._snapshot_history("task", id_, "delete")
        return super().delete(id_)

    def get_subtasks(self, parent_id: int) -> List[Task]:
        return self.get_all(parent_task_id=parent_id)

    def get_recurring(self) -> List[Task]:
        rows = self._fetch_all("""
            SELECT t.*, c.name AS category_name FROM tasks t
            LEFT JOIN categories c ON c.id=t.category_id
            WHERE t.recurrence != 'none' AND t.status NOT IN ('cancelled')""")
        return [self._row_to_task(r) for r in rows]

    def get_stats(self) -> Dict[str, int]:
        row = self._fetch_one("""
            SELECT
              COUNT(*) AS total,
              SUM(status='done') AS done,
              SUM(status='todo') AS todo,
              SUM(status='in_progress') AS in_progress,
              SUM(due_date = date('now') AND status NOT IN ('done','cancelled')) AS due_today,
              SUM(due_date < date('now') AND status NOT IN ('done','cancelled')) AS overdue
            FROM tasks""")
        return dict(row) if row else {}
