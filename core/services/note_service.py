"""core/services/note_service.py"""

from typing import List, Optional
from core.repositories.note_repository import NoteRepository
from core.domain.models import Note
from utils.validator import require

_repo = NoteRepository()


def create_note(title: str, **kwargs) -> Note:
    title = require(title, "عنوان یادداشت")
    return _repo.create(title, **kwargs)


def update_note(id_: int, **kwargs) -> bool:
    if "title" in kwargs:
        kwargs["title"] = require(kwargs["title"], "عنوان یادداشت")
    return _repo.update(id_, **kwargs)


def delete_note(id_: int) -> bool:
    return _repo.delete(id_)


def get_notes(parent_id: Optional[int] = None) -> List[Note]:
    return _repo.get_all(parent_id)


def get_note(id_: int) -> Optional[Note]:
    return _repo.get_by_id(id_)


def toggle_pin(id_: int) -> bool:
    note = _repo.get_by_id(id_)
    if note:
        return _repo.update(id_, is_pinned=0 if note.is_pinned else 1)
    return False


def search_notes(query: str) -> List[Note]:
    return _repo.search(query)
