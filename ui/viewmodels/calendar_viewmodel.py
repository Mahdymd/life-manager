"""
ui/viewmodels/calendar_viewmodel.py

ViewModel صفحه‌ی تقویم. الگو از task_list_viewmodel.py.

به‌روزرسانی: قبلاً این ViewModel مستقیم به CalendarRepository وصل بود
(چون core.services.calendar_service وجود نداشت). حالا که آن سرویس
ساخته شده، این فایل هم مثل بقیه‌ی ViewModel ها فقط از لایه‌ی Service
عبور می‌کند — معماری کل پروژه یکدست شد.
"""

from __future__ import annotations
from typing import List
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.services.calendar_service import (
    get_events_by_month,
    create_event,
    update_event,
)


class CalendarViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی تقویم.

    Signals:
        events_changed(list): رویدادهای ماه جاری.
    """

    events_changed = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._year: int = 0
        self._month: int = 0

    def load(self, year: int, month: int) -> None:
        """رویدادهای یک ماه شمسی مشخص را بارگذاری می‌کند و آن را به‌عنوان
        «ماه جاری» برای reload های بعدی (بعد از add/update) به‌خاطر می‌سپارد."""
        self._year, self._month = year, month
        self.run_async(get_events_by_month, self._on_events_loaded, year, month)

    def _on_events_loaded(self, events: List) -> None:
        self.events_changed.emit(events)

    def _reload_current(self) -> None:
        if self._year and self._month:
            self.load(self._year, self._month)

    def add_event(self, **data) -> None:
        self.run_async(create_event, lambda _r: self._reload_current(), **data)

    def update_event(self, id_: int, **data) -> None:
        self.run_async(update_event, lambda _r: self._reload_current(), id_, **data)
