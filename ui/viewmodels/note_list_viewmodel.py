"""
ui/viewmodels/note_list_viewmodel.py

ViewModel صفحه‌ی یادداشت‌ها (Knowledge Base). الگو از task_list_viewmodel.py.
"""

from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.domain.models import Note
from core.services.note_service import (
    get_notes,
    search_notes,
    create_note,
    update_note,
    delete_note,
    toggle_pin,
)


class NoteListViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی یادداشت‌ها.

    Signals:
        notes_changed(list[Note])
        note_created(object): یادداشت تازه‌ساخته‌شده (برای انتخاب خودکار در View).
    """

    notes_changed = Signal(list)
    note_created = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._search_query: Optional[str] = None

    def load(self, search: Optional[str] = None) -> None:
        self._search_query = search.strip() if search and search.strip() else None
        if self._search_query:
            self.run_async(search_notes, self._on_notes_loaded, self._search_query)
        else:
            self.run_async(get_notes, self._on_notes_loaded)

    def _on_notes_loaded(self, notes: List[Note]) -> None:
        self.notes_changed.emit(notes)

    def create(self, title: str = "یادداشت جدید") -> None:
        self.run_async(create_note, self._on_created, title)

    def _on_created(self, note: Note) -> None:
        self.note_created.emit(note)
        self.load(self._search_query)

    def update(self, id_: int, **data) -> None:
        self.run_async(update_note, lambda _r: self.load(self._search_query), id_, **data)

    def toggle_pin(self, id_: int) -> None:
        self.run_async(toggle_pin, lambda _r: self.load(self._search_query), id_)

    def remove(self, id_: int) -> None:
        self.run_async(delete_note, lambda _r: self.load(self._search_query), id_)
