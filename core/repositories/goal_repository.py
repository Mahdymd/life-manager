"""core/repositories/goal_repository.py"""

from typing import List, Optional, Dict
from core.repositories.base_repository import BaseRepository
from core.domain.models import Goal, GoalKeyResult
from core.domain.enums import GoalHorizon, GoalStatus, GoalProgressMode


class GoalRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("goals")

    def _row_to_goal(self, row) -> Goal:
        d = self._row_to_dict(row)
        return Goal(
            id=d["id"], title=d["title"], description=d.get("description"),
            horizon=GoalHorizon(d["horizon"]),
            category_id=d.get("category_id"), parent_goal_id=d.get("parent_goal_id"),
            start_date=d.get("start_date"), target_date=d.get("target_date"),
            status=GoalStatus(d.get("status","active")),
            progress_mode=GoalProgressMode(d.get("progress_mode","auto")),
            manual_progress=d.get("manual_progress",0.0),
            sort_order=d.get("sort_order",0),
            created_at=d["created_at"], updated_at=d["updated_at"],
            category_name=d.get("category_name"),
        )

    def get_by_id(self, id_: int) -> Optional[Goal]:
        row = self._fetch_one("""
            SELECT g.*, c.name AS category_name FROM goals g
            LEFT JOIN categories c ON c.id=g.category_id WHERE g.id=?""", (id_,))
        return self._row_to_goal(row) if row else None

    def get_all(self, horizon: Optional[str] = None,
                status: Optional[str] = None,
                parent_id: Optional[int] = None) -> List[Goal]:
        wheres, params = [], []
        if horizon: wheres.append("g.horizon=?"); params.append(horizon)
        if status:  wheres.append("g.status=?");  params.append(status)
        if parent_id is not None:
            wheres.append("g.parent_goal_id=?"); params.append(parent_id)
        else:
            wheres.append("g.parent_goal_id IS NULL")
        where_sql = " AND ".join(wheres) if wheres else "1=1"
        rows = self._fetch_all(f"""
            SELECT g.*, c.name AS category_name FROM goals g
            LEFT JOIN categories c ON c.id=g.category_id
            WHERE {where_sql} ORDER BY g.sort_order, g.created_at""", tuple(params))
        return [self._row_to_goal(r) for r in rows]

    def get_children(self, parent_id: int) -> List[Goal]:
        return self.get_all(parent_id=parent_id)

    def create(self, title: str, horizon: str, **kwargs) -> Goal:
        id_ = self._insert({"title": title, "horizon": horizon, **kwargs})
        return self.get_by_id(id_)

    def update(self, id_: int, **kwargs) -> bool:
        return self._update(id_, kwargs)

    def get_key_results(self, goal_id: int) -> List[GoalKeyResult]:
        rows = self._fetch_all(
            "SELECT * FROM goal_key_results WHERE goal_id=? ORDER BY id", (goal_id,))
        result = []
        for r in rows:
            d = self._row_to_dict(r)
            result.append(GoalKeyResult(
                id=d["id"], goal_id=d["goal_id"], title=d["title"],
                target=d["target"], current=d["current"], unit=d.get("unit"),
                created_at=d["created_at"], updated_at=d["updated_at"],
            ))
        return result

    def upsert_key_result(self, goal_id: int, title: str,
                          target: float, current: float = 0,
                          unit: str = None, kr_id: int = None) -> int:
        now = self._now()
        if kr_id:
            self._conn().execute("""
                UPDATE goal_key_results SET title=?,target=?,current=?,unit=?,updated_at=?
                WHERE id=?""", (title, target, current, unit, now, kr_id))
        else:
            cur = self._conn().execute("""
                INSERT INTO goal_key_results(goal_id,title,target,current,unit,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)""", (goal_id, title, target, current, unit, now, now))
            kr_id = cur.lastrowid
        from core.database.connection import commit
        commit()
        return kr_id

    def delete_key_result(self, kr_id: int) -> bool:
        cur = self._conn().execute(
            "DELETE FROM goal_key_results WHERE id=?", (kr_id,))
        from core.database.connection import commit
        commit()
        return cur.rowcount > 0

    def get_stats(self) -> Dict:
        row = self._fetch_one("""
            SELECT COUNT(*) AS total,
              COALESCE(SUM(status='active'), 0) AS active,
              COALESCE(SUM(status='done'), 0) AS done,
              COALESCE(SUM(status='paused'), 0) AS paused
            FROM goals""")
        d = dict(row) if row else {}
        return {k: (v or 0) for k, v in d.items()}
