"""core/repositories/journal_repository.py"""

from typing import List, Optional
from core.repositories.base_repository import BaseRepository
from core.domain.models import JournalEntry


class JournalRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("journal_entries")

    def _to_entry(self, row) -> JournalEntry:
        d = self._row_to_dict(row)
        return JournalEntry(**{k: v for k, v in d.items()
                               if k in JournalEntry.__dataclass_fields__})

    def get_by_date(self, date: str) -> Optional[JournalEntry]:
        row = self._fetch_one("SELECT * FROM journal_entries WHERE date=?", (date,))
        return self._to_entry(row) if row else None

    def get_recent(self, limit: int = 30) -> List[JournalEntry]:
        rows = self._fetch_all(
            "SELECT * FROM journal_entries ORDER BY date DESC LIMIT ?", (limit,))
        return [self._to_entry(r) for r in rows]

    def upsert(self, date: str, **kwargs) -> JournalEntry:
        existing = self.get_by_date(date)
        now = self._now()
        if existing:
            self._snapshot_history("journal_entry", existing.id, "update")
            self._update(existing.id, kwargs)
        else:
            self._insert({"date": date, **kwargs})
        return self.get_by_date(date)

    def update(self, id_: int, **kwargs) -> bool:
        """به‌روزرسانی مستقیم بر اساس id (نه date) — برای هم‌خوانی با
        بقیه‌ی repository ها (مثل TaskRepository.update) و برای اینکه
        core.services.history_service.restore_snapshot بتواند نسخه‌های
        قبلی را بازگرداند. قبلاً این متد وجود نداشت و باعث خطای واقعی
        هنگام بازگردانی نسخه‌ی قدیمی یک یادداشت روزانه می‌شد (تأیید‌شده
        با تست end-to-end)."""
        self._snapshot_history("journal_entry", id_, "update")
        return self._update(id_, kwargs)

    def get_mood_data(self, from_date: str, to_date: str) -> List:
        rows = self._fetch_all("""
            SELECT date, mood, energy FROM journal_entries
            WHERE date BETWEEN ? AND ? AND mood IS NOT NULL
            ORDER BY date""", (from_date, to_date))
        return [dict(r) for r in rows]

    def search(self, query: str) -> List[JournalEntry]:
        """جستجوی متن کامل با FTS5 (journal_fts، ساخته‌شده در migration
        v002). قبلاً این متد از LIKE ساده استفاده می‌کرد که هم کندتر بود
        و هم رتبه‌بندی نداشت."""
        words = [w.replace('"', '""') for w in query.strip().split() if w]
        if not words:
            return []
        match_expr = " AND ".join(f'"{w}"*' for w in words)
        try:
            rows = self._fetch_all("""
                SELECT j.* FROM journal_fts
                JOIN journal_entries j ON j.id = journal_fts.rowid
                WHERE journal_fts MATCH ?
                ORDER BY bm25(journal_fts) LIMIT 20""", (match_expr,))
            return [self._to_entry(r) for r in rows]
        except Exception:
            # fallback ایمن اگر به هر دلیل FTS در دسترس نبود (مثلاً
            # دیتابیس خیلی قدیمی که هنوز migration v002 روی آن اجرا نشده)
            rows = self._fetch_all("""
                SELECT * FROM journal_entries WHERE content LIKE ?
                ORDER BY date DESC LIMIT 20""", (f"%{query}%",))
            return [self._to_entry(r) for r in rows]
