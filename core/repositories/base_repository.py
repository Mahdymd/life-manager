"""
core/repositories/base_repository.py
کلاس پایه repository — متدهای مشترک CRUD.
"""

import sqlite3
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from datetime import datetime
from core.database.connection import get_connection, commit

logger = logging.getLogger("life_manager.repo")
T = TypeVar("T")


class BaseRepository:
    def __init__(self, table: str) -> None:
        self._table = table

    def _conn(self) -> sqlite3.Connection:
        return get_connection()

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return dict(row) if row else {}

    def count(self, where: str = "", params: Tuple = ()) -> int:
        sql = f"SELECT COUNT(*) FROM {self._table}"
        if where:
            sql += f" WHERE {where}"
        row = self._conn().execute(sql, params).fetchone()
        return row[0] if row else 0

    def exists(self, id_: int) -> bool:
        row = self._conn().execute(
            f"SELECT 1 FROM {self._table} WHERE id=?", (id_,)
        ).fetchone()
        return row is not None

    def delete(self, id_: int) -> bool:
        cur = self._conn().execute(
            f"DELETE FROM {self._table} WHERE id=?", (id_,)
        )
        commit()
        return cur.rowcount > 0

    def _fetch_one(self, sql: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        return self._conn().execute(sql, params).fetchone()

    def _fetch_all(self, sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
        return self._conn().execute(sql, params).fetchall()

    def _insert(self, data: Dict[str, Any]) -> int:
        data.setdefault("created_at", self._now())
        data.setdefault("updated_at", self._now())
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        cur = self._conn().execute(
            f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders})",
            tuple(data.values()),
        )
        commit()
        return cur.lastrowid

    def _update(self, id_: int, data: Dict[str, Any]) -> bool:
        data["updated_at"] = self._now()
        sets = ", ".join(f"{k}=?" for k in data)
        cur = self._conn().execute(
            f"UPDATE {self._table} SET {sets} WHERE id=?",
            (*data.values(), id_),
        )
        commit()
        return cur.rowcount > 0

    # ────────────────────────────────────────────────────────────
    # Version history (time-travel) — فقط برای entity های "کلیدی"
    # طبق اسپک بخش ۷.۴ استفاده می‌شود (فعلاً: task و journal_entry).
    # زیرکلاس‌ها باید قبل از فراخوانی _update/delete این متد را صدا
    # بزنند تا snapshot قبل از تغییر ثبت شود (snapshot-before-write).
    # ────────────────────────────────────────────────────────────
    def _snapshot_history(self, entity_type: str, id_: int, change_type: str) -> None:
        """وضعیت فعلی رکورد (قبل از تغییر) را در entity_history ذخیره می‌کند.

        این متد silently نادیده می‌گیرد اگر رکورد پیدا نشود یا جدول
        entity_history هنوز موجود نباشد (مثلاً روی دیتابیس خیلی قدیمی
        که migration v002 هنوز اجرا نشده) — چون snapshot ثانویه است و
        نباید عملیات اصلی CRUD را fail کند.
        """
        import json
        try:
            row = self._fetch_one(f"SELECT * FROM {self._table} WHERE id=?", (id_,))
            if not row:
                return
            snapshot = json.dumps(self._row_to_dict(row), ensure_ascii=False, default=str)
            self._conn().execute(
                """INSERT INTO entity_history
                   (entity_type, entity_id, snapshot_json, change_type, changed_at)
                   VALUES (?,?,?,?,?)""",
                (entity_type, id_, snapshot, change_type, self._now()),
            )
            commit()
        except Exception:
            logger.warning(
                "History snapshot skipped for %s#%s (entity_history unavailable?)",
                entity_type, id_, exc_info=True)
