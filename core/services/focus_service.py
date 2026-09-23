"""core/services/focus_service.py"""

from typing import List, Optional, Dict
from datetime import datetime
from core.repositories.focus_repository import FocusRepository
from core.domain.models import FocusSession
from core.domain.enums import FocusSessionType, FocusSessionStatus
from utils.date_utils import now_iso

_repo = FocusRepository()


def start_session(type_: str, planned_min: int, task_id: int = None) -> FocusSession:
    return _repo.add(type_, planned_min, now_iso(), task_id=task_id)


def complete_session(session_id: int, actual_min: int, note: str = None) -> bool:
    return _repo.update(session_id,
        status="completed", actual_min=actual_min,
        ended_at=now_iso(), note=note)


def interrupt_session(session_id: int, actual_min: int) -> bool:
    return _repo.update(session_id,
        status="interrupted", actual_min=actual_min, ended_at=now_iso())


def get_today_sessions() -> List[FocusSession]:
    return _repo.get_today_sessions()


def get_focus_stats() -> Dict:
    return _repo.get_stats()
