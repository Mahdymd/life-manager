"""core/services/calendar_service.py — Business logic تقویم.

این فایل گپ معماری M5 در گزارش ممیزی فاز ۰ را می‌بندد: قبلاً تقویم
تنها ماژولی بود که لایه‌ی service نداشت و ViewModel مستقیم به
CalendarRepository وصل می‌شد. الگوی این فایل دقیقاً از task_service.py
پیروی می‌کند تا معماری کل پروژه یکدست بماند.
"""

import logging
from typing import List, Optional
from core.repositories.calendar_repository import CalendarRepository
from core.domain.models import CalendarEvent
from utils.validator import require

logger = logging.getLogger("life_manager.calendar_service")
_repo = CalendarRepository()


def get_events_by_month(year: int, month: int) -> List[CalendarEvent]:
    return _repo.get_by_month(year, month)


def get_events_by_date(date_str: str) -> List[CalendarEvent]:
    return _repo.get_by_date(date_str)


def create_event(title: str, date: str, **kwargs) -> CalendarEvent:
    title = require(title, "عنوان رویداد")
    date = require(date, "تاریخ رویداد")
    return _repo.add(title, date, **kwargs)


def update_event(id_: int, **kwargs) -> bool:
    if "title" in kwargs:
        kwargs["title"] = require(kwargs["title"], "عنوان رویداد")
    return _repo.update(id_, **kwargs)


def delete_event(id_: int) -> bool:
    return _repo.delete(id_)
