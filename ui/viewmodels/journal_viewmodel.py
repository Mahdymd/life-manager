"""
ui/viewmodels/journal_viewmodel.py

ViewModel صفحه‌ی یادداشت روزانه. الگو از task_list_viewmodel.py.
"""

from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.domain.models import JournalEntry
from core.services import history_service
from core.services.journal_service import get_recent, save_entry, search_journal


def _fetch_entry(date_str: str) -> Optional[JournalEntry]:
    """در worker thread اجرا می‌شود؛ import محلی برای جلوگیری از وابستگی
    چرخه‌ای در سطح ماژول."""
    from core.repositories.journal_repository import JournalRepository
    return JournalRepository().get_by_date(date_str)


class JournalViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی یادداشت روزانه.

    Signals:
        entries_changed(list[JournalEntry]): لیست تاریخچه (سایدبار).
        entry_loaded(object): یک JournalEntry یا None، برای تاریخ انتخاب‌شده.
        search_results_changed(list[JournalEntry]): نتایج جستجوی متن کامل.
    """

    entries_changed = Signal(list)
    entry_loaded = Signal(object)
    search_results_changed = Signal(list)
    version_history_loaded = Signal(list)

    def load_history(self, limit: int = 60) -> None:
        self.run_async(get_recent, self._on_entries_loaded, limit)

    def _on_entries_loaded(self, entries: List[JournalEntry]) -> None:
        self.entries_changed.emit(entries)

    def load_entry(self, date_str: str) -> None:
        self.run_async(_fetch_entry, self._on_entry_loaded, date_str)

    def _on_entry_loaded(self, entry) -> None:
        self.entry_loaded.emit(entry)

    def search(self, query: str) -> None:
        """جستجوی متن کامل (FTS5) در همه‌ی یادداشت‌های روزانه — طبق
        بخش ۴ اسپک: "Journal: ... full‑text search". اگر query خالی
        باشد، به‌جای جستجو، دوباره تاریخچه‌ی عادی را نشان می‌دهد."""
        if not query or not query.strip():
            self.load_history()
            return
        self.run_async(search_journal, self.search_results_changed.emit, query)

    def save(self, date_str: str, **kwargs) -> None:
        self.run_async(save_entry, lambda _r: self.load_history(), date_str, **kwargs)

    # ────────────────────────────────────────────────────────────
    # Version History — طبق بخش ۶ اسپک: "Version History: restore
    # previous versions of tasks/journal entries"
    # ────────────────────────────────────────────────────────────
    def load_version_history(self, date_str: str) -> None:
        def _fetch():
            entry = _fetch_entry(date_str)
            if not entry:
                return []
            return history_service.get_history("journal_entry", entry.id)
        self.run_async(_fetch, self.version_history_loaded.emit)

    def restore_version(self, history_id: int, date_str: str) -> None:
        def _on_restored(_result):
            self.load_history()
            self.load_entry(date_str)
        self.run_async(history_service.restore_snapshot, _on_restored, history_id)
