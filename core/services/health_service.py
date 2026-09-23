"""core/services/health_service.py"""

from typing import List, Dict, Optional
from core.repositories.health_repository import HealthRepository
from utils.date_utils import today_iso
from utils.validator import require_positive

_repo = HealthRepository()


def log_weight(value: float, date: str = None, note: str = None) -> None:
    require_positive(value, "وزن")
    _repo.upsert_metric(date or today_iso(), "weight", value, note)


def log_water(glasses: int, date: str = None) -> None:
    _repo.upsert_metric(date or today_iso(), "water", glasses)


def log_sleep(hours: float, quality: int = None, date: str = None) -> None:
    d = date or today_iso()
    _repo.upsert_metric(d, "sleep_hours", hours)
    if quality is not None:
        _repo.upsert_metric(d, "sleep_quality", quality)


def log_workout(type_: str, duration_min: int = None,
                calories: int = None, note: str = None, date: str = None) -> None:
    _repo.add_workout(date or today_iso(), type_,
                      duration_min=duration_min, calories=calories, note=note)


def get_today(date: str = None) -> Dict[str, float]:
    return _repo.get_today_metrics(date or today_iso())


def get_weight_history(limit: int = 30) -> List[Dict]:
    return _repo.get_metric_history("weight", limit)


def get_sleep_history(limit: int = 30) -> List[Dict]:
    return _repo.get_metric_history("sleep_hours", limit)


def get_recent_workouts(limit: int = 10) -> List[Dict]:
    return _repo.get_workouts(limit)
