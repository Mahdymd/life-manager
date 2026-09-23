"""utils/validator.py — validation های مشترک."""

from typing import Optional
from core.domain.exceptions import RequiredFieldError, InvalidValueError


def require(value: Optional[str], field: str) -> str:
    if not value or not str(value).strip():
        raise RequiredFieldError(field)
    return str(value).strip()


def require_positive(value: float, field: str) -> float:
    if value is None or value <= 0:
        raise InvalidValueError(field, value, "عدد مثبت")
    return value


def require_range(value: int, field: str, lo: int, hi: int) -> int:
    if value < lo or value > hi:
        raise InvalidValueError(field, value, f"{lo} تا {hi}")
    return value
