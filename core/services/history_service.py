"""core/services/history_service.py — Version History / Time-Travel.

مطابق بخش ۷.۴ اسپک: "Version history: maintain a history table for key
entities (tasks, journal) enabling time-travel and undo."

این سرویس روی جدول entity_history (که در migration v002 ساخته شده)
کار می‌کند و دو قابلیت اصلی می‌دهد:
  1. get_history(...)      → لیست نسخه‌های قبلی یک رکورد.
  2. restore_snapshot(...) → بازگردانی رکورد به یکی از نسخه‌های قبلی.

نکته‌ی طراحی: خودِ عملیات restore هم یک "update" عادی است، پس از طریق
TaskRepository.update()/JournalRepository مسیر عادی عبور می‌کند و
بنابراین خودش هم یک snapshot جدید قبل از بازگردانی ثبت می‌کند — یعنی
restore کردن هم قابل "undo" است (چیزی گم نمی‌شود).
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from typing import List, Optional
from core.database.connection import get_connection
from core.domain.exceptions import AppError

logger = logging.getLogger("life_manager.history")

_ALLOWED_ENTITY_TYPES = {"task", "journal_entry"}


@dataclass
class HistoryEntry:
    id: int
    entity_type: str
    entity_id: int
    change_type: str      # "update" | "delete"
    changed_at: str
    snapshot: dict


def get_history(entity_type: str, entity_id: int, limit: int = 20) -> List[HistoryEntry]:
    """لیست نسخه‌های قبلیِ یک رکورد را از جدیدترین به قدیمی‌ترین برمی‌گرداند."""
    if entity_type not in _ALLOWED_ENTITY_TYPES:
        raise AppError(f"نوع entity نامعتبر برای تاریخچه: {entity_type}")

    conn = get_connection()
    rows = conn.execute(
        """SELECT id, entity_type, entity_id, snapshot_json, change_type, changed_at
           FROM entity_history
           WHERE entity_type=? AND entity_id=?
           ORDER BY changed_at DESC, id DESC
           LIMIT ?""",
        (entity_type, entity_id, limit),
    ).fetchall()

    result = []
    for r in rows:
        try:
            snapshot = json.loads(r["snapshot_json"])
        except (json.JSONDecodeError, TypeError):
            snapshot = {}
        result.append(HistoryEntry(
            id=r["id"], entity_type=r["entity_type"], entity_id=r["entity_id"],
            change_type=r["change_type"], changed_at=r["changed_at"], snapshot=snapshot,
        ))
    return result


def _repository_for(entity_type: str):
    """Repository مربوط به این نوع entity را برمی‌گرداند (lazy import برای
    جلوگیری از circular import)."""
    if entity_type == "task":
        from core.repositories.task_repository import TaskRepository
        return TaskRepository()
    if entity_type == "journal_entry":
        from core.repositories.journal_repository import JournalRepository
        return JournalRepository()
    raise AppError(f"نوع entity نامعتبر برای تاریخچه: {entity_type}")


# ستون‌هایی که هرگز نباید هنگام restore بازنویسی شوند (شناسه‌ها/timestamp های سیستمی)
_PROTECTED_COLUMNS = {"id", "created_at", "updated_at"}


def restore_snapshot(history_id: int) -> bool:
    """رکورد را به وضعیت ثبت‌شده در یک ردیف مشخص از entity_history برمی‌گرداند.

    - اگر change_type == 'update': یعنی رکورد در آن لحظه هنوز وجود داشته؛
      snapshot را با UPDATE روی رکورد فعلی اعمال می‌کنیم.
    - اگر change_type == 'delete': یعنی رکورد در آن لحظه حذف شده؛ برای
      "احیا"ی آن یک رکورد جدید با همان داده‌ها INSERT می‌کنیم (چون sqlite
      autoincrement همان id قدیمی را تضمین نمی‌دهد و نباید بدهد).

    خروجی: True در صورت موفقیت.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM entity_history WHERE id=?", (history_id,)
    ).fetchone()
    if not row:
        raise AppError("نسخه‌ی تاریخچه‌ی موردنظر پیدا نشد.")

    entity_type = row["entity_type"]
    entity_id = row["entity_id"]
    change_type = row["change_type"]
    try:
        snapshot = json.loads(row["snapshot_json"])
    except (json.JSONDecodeError, TypeError):
        raise AppError("داده‌ی این نسخه‌ی تاریخچه معتبر نیست.")

    repo = _repository_for(entity_type)
    clean_fields = {k: v for k, v in snapshot.items() if k not in _PROTECTED_COLUMNS}

    if change_type == "update":
        if not repo.exists(entity_id):
            # رکورد بین این مدت حذف شده؛ باید احیا شود نه update
            return _reinsert(repo, entity_type, snapshot)
        repo.update(entity_id, **clean_fields)
        logger.info("Restored %s#%s from history #%s", entity_type, entity_id, history_id)
        return True

    # change_type == "delete" → احیای رکورد حذف‌شده
    return _reinsert(repo, entity_type, snapshot)


def _reinsert(repo, entity_type: str, snapshot: dict) -> bool:
    """رکورد حذف‌شده را با یک id جدید دوباره INSERT می‌کند (احیا)."""
    fields = {k: v for k, v in snapshot.items() if k not in _PROTECTED_COLUMNS}
    if entity_type == "task":
        title = fields.pop("title", "بدون عنوان")
        repo.create(title, **fields)
    elif entity_type == "journal_entry":
        date = fields.pop("date", None)
        if not date:
            raise AppError("تاریخ یادداشت روزانه در این نسخه موجود نیست.")
        repo.upsert(date, **fields)
    else:
        return False
    logger.info("Re-created deleted %s from history snapshot", entity_type)
    return True
