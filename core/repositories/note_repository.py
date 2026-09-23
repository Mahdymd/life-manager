"""core/repositories/note_repository.py"""

from typing import List, Optional
from core.repositories.base_repository import BaseRepository
from core.domain.models import Note


class NoteRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("notes")

    def _to_note(self, row) -> Note:
        d = self._row_to_dict(row)
        return Note(
            id=d["id"], title=d["title"], content=d.get("content"),
            parent_id=d.get("parent_id"), is_pinned=bool(d.get("is_pinned",0)),
            sort_order=d.get("sort_order",0),
            created_at=d["created_at"], updated_at=d["updated_at"],
            child_count=d.get("child_count",0),
        )

    def get_all(self, parent_id: Optional[int] = None) -> List[Note]:
        if parent_id is None:
            where = "n.parent_id IS NULL"
            params: tuple = ()
        else:
            where = "n.parent_id=?"
            params = (parent_id,)
        rows = self._fetch_all(f"""
            SELECT n.*,
              (SELECT COUNT(*) FROM notes c WHERE c.parent_id=n.id) AS child_count
            FROM notes n WHERE {where}
            ORDER BY n.is_pinned DESC, n.sort_order, n.updated_at DESC""", params)
        return [self._to_note(r) for r in rows]

    def get_by_id(self, id_: int) -> Optional[Note]:
        row = self._fetch_one("""
            SELECT n.*,
              (SELECT COUNT(*) FROM notes c WHERE c.parent_id=n.id) AS child_count
            FROM notes n WHERE n.id=?""", (id_,))
        return self._to_note(row) if row else None

    def create(self, title: str, **kwargs) -> Note:
        id_ = self._insert({"title": title, **kwargs})
        return self.get_by_id(id_)

    def update(self, id_: int, **kwargs) -> bool:
        return self._update(id_, kwargs)

    def search(self, query: str) -> List[Note]:
        rows = self._fetch_all("""
            SELECT n.*, 0 AS child_count FROM notes n
            WHERE n.title LIKE ? OR n.content LIKE ?
            ORDER BY n.updated_at DESC LIMIT 20""",
            (f"%{query}%", f"%{query}%"))
        return [self._to_note(r) for r in rows]
