"""core/repositories/tag_repository.py"""

from typing import List
from core.repositories.base_repository import BaseRepository
from core.domain.models import Tag
from core.database.connection import commit


class TagRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("tags")

    def _to_tag(self, row) -> Tag:
        d = self._row_to_dict(row)
        return Tag(id=d["id"], name=d["name"], color=d.get("color", "#6366f1"),
                   created_at=d["created_at"], updated_at=d["updated_at"])

    def get_all(self) -> List[Tag]:
        rows = self._fetch_all("SELECT * FROM tags ORDER BY name")
        return [self._to_tag(r) for r in rows]

    def create(self, name: str, color: str = "#6366f1") -> Tag:
        id_ = self._insert({"name": name, "color": color})
        row = self._fetch_one("SELECT * FROM tags WHERE id=?", (id_,))
        return self._to_tag(row)

    def tag_entity(self, tag_id: int, entity_type: str, entity_id: int) -> None:
        try:
            self._conn().execute("""
                INSERT OR IGNORE INTO taggables(tag_id,entity_type,entity_id)
                VALUES(?,?,?)""", (tag_id, entity_type, entity_id))
            commit()
        except Exception:
            pass

    def get_entity_tags(self, entity_type: str, entity_id: int) -> List[Tag]:
        rows = self._fetch_all("""
            SELECT t.* FROM tags t
            JOIN taggables tb ON tb.tag_id=t.id
            WHERE tb.entity_type=? AND tb.entity_id=?""", (entity_type, entity_id))
        return [self._to_tag(r) for r in rows]

    def get_category_all(self, module: str) -> List:
        rows = self._fetch_all("""
            SELECT * FROM categories WHERE module=? ORDER BY sort_order,name""", (module,))
        return [dict(r) for r in rows]

    def upsert_category(self, module: str, name: str, color: str = None) -> int:
        now = self._now()
        try:
            cur = self._conn().execute("""
                INSERT INTO categories(module,name,color,created_at) VALUES(?,?,?,?)""",
                (module, name, color, now))
            commit()
            return cur.lastrowid
        except Exception:
            row = self._fetch_one(
                "SELECT id FROM categories WHERE module=? AND name=?", (module, name))
            return row["id"] if row else -1
