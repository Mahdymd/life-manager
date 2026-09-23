"""
ui/viewmodels/goal_list_viewmodel.py

ViewModel صفحه‌ی اهداف. الگو از task_list_viewmodel.py.
"""

from __future__ import annotations
from typing import Dict, List
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.domain.models import Goal, GoalKeyResult
from core.services.goal_service import (
    get_all_goals,
    create_goal,
    update_goal,
    delete_goal,
    generate_catchup_plan,
    get_key_results,
    upsert_key_result,
    delete_key_result,
)


def _fetch_catchup_plans(goal_ids: List[int]) -> Dict[int, str]:
    """در worker thread اجرا می‌شود؛ برای هر هدف پلن جبران عقب‌ماندگی
    (اگر لازم باشد) را محاسبه می‌کند."""
    result = {}
    for gid in goal_ids:
        plan = generate_catchup_plan(gid)
        if plan:
            result[gid] = plan
    return result


class GoalListViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی اهداف.

    Signals:
        goals_changed(list[Goal])
        catchup_plans_changed(dict): {goal_id: plan_text} — فقط اهدافی
            که واقعاً عقب‌افتاده‌اند در این دیکشنری هستند.
        milestones_loaded(int, list): goal_id، لیست GoalKeyResult های آن.
    """

    goals_changed = Signal(list)
    catchup_plans_changed = Signal(dict)
    milestones_loaded = Signal(int, list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._goals: List[Goal] = []

    @property
    def goals(self) -> List[Goal]:
        return self._goals

    def load(self) -> None:
        self.run_async(self._fetch_active_goals, self._on_goals_loaded)

    @staticmethod
    def _fetch_active_goals() -> List[Goal]:
        return get_all_goals(status="active")

    def _on_goals_loaded(self, goals: List[Goal]) -> None:
        self._goals = goals
        self.goals_changed.emit(goals)
        if goals:
            goal_ids = [g.id for g in goals]
            self.run_async(_fetch_catchup_plans, self.catchup_plans_changed.emit, goal_ids)

    def create(self, **data) -> None:
        self.run_async(create_goal, lambda _r: self.load(), **data)

    def update(self, id_: int, **data) -> None:
        self.run_async(update_goal, lambda _r: self.load(), id_, **data)

    def remove(self, id_: int) -> None:
        self.run_async(delete_goal, lambda _r: self.load(), id_)

    # ────────────────────────────────────────────────────────────
    # Milestones (Key Results) — طبق بخش ۴ اسپک: "Goals: ... milestones"
    # ────────────────────────────────────────────────────────────
    def load_milestones(self, goal_id: int) -> None:
        self.run_async(
            get_key_results,
            lambda krs: self.milestones_loaded.emit(goal_id, krs),
            goal_id,
        )

    def save_milestone(self, goal_id: int, **data) -> None:
        def _on_saved(_result):
            self.load_milestones(goal_id)
            self.load()
        self.run_async(upsert_key_result, _on_saved, goal_id, **data)

    def remove_milestone(self, kr_id: int, goal_id: int) -> None:
        def _on_removed(_result):
            self.load_milestones(goal_id)
            self.load()
        self.run_async(delete_key_result, _on_removed, kr_id)
