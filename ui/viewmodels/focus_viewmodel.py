"""
ui/viewmodels/focus_viewmodel.py

ViewModel صفحه‌ی فوکوس/Pomodoro. الگو از task_list_viewmodel.py.

نکته: چون تایمر خودش (QTimer در View) نیازی به دیتابیس ندارد و نباید
منتظر آن بماند، start_session/complete_session به‌صورت fire-and-forget
async هستند — تایمر بصری بلافاصله شروع می‌شود و session_id واقعی چند
صدم ثانیه بعد (وقتی worker تمام شد) از طریق سیگنال session_started
به View می‌رسد.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.domain.models import FocusSession
from core.services.focus_service import (
    start_session,
    complete_session,
    get_today_sessions,
    get_focus_stats,
)


class FocusViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی فوکوس.

    Signals:
        stats_changed(dict)
        sessions_changed(list[FocusSession])
        session_started(object): FocusSession تازه‌ساخته‌شده یا None در صورت خطا.
    """

    stats_changed = Signal(dict)
    sessions_changed = Signal(list)
    session_started = Signal(object)

    def load(self) -> None:
        self.run_async(get_focus_stats, self._on_stats_loaded)
        self.run_async(get_today_sessions, self._on_sessions_loaded)

    def _on_stats_loaded(self, stats: Dict) -> None:
        self.stats_changed.emit(stats)

    def _on_sessions_loaded(self, sessions: List[FocusSession]) -> None:
        self.sessions_changed.emit(sessions)

    def start_session(self, type_: str, planned_min: int) -> None:
        """جلسه‌ی جدید را async ثبت می‌کند؛ تایمر بصری نباید منتظر این
        عملیات بماند (View بلافاصله بعد از فراخوانی این متد، شمارش
        معکوس را شروع می‌کند)."""
        def _safe_start():
            try:
                return start_session(type_, planned_min)
            except Exception:
                return None
        self.run_async(_safe_start, self.session_started.emit)

    def complete_session(self, session_id: int, actual_min: int) -> None:
        self.run_async(complete_session, lambda _r: self.load(), session_id, actual_min)
