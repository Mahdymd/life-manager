"""core/services/journal_service.py"""

import json
from typing import List, Optional
from core.repositories.journal_repository import JournalRepository
from core.domain.models import JournalEntry
from utils.date_utils import today_iso

_repo = JournalRepository()


def get_or_create_today() -> JournalEntry:
    today = today_iso()
    entry = _repo.get_by_date(today)
    if not entry:
        entry = _repo.upsert(today)
    return entry


def save_entry(date: str, content: str = None, mood: int = None,
               energy: int = None, gratitude: List[str] = None,
               wins: List[str] = None) -> JournalEntry:
    kwargs = {}
    if content  is not None: kwargs["content"]   = content
    if mood     is not None: kwargs["mood"]      = mood
    if energy   is not None: kwargs["energy"]    = energy
    if gratitude is not None:
        kwargs["gratitude"] = json.dumps(gratitude, ensure_ascii=False)
    if wins is not None:
        kwargs["wins"] = json.dumps(wins, ensure_ascii=False)
    return _repo.upsert(date, **kwargs)


def get_recent(limit: int = 30) -> List[JournalEntry]:
    return _repo.get_recent(limit)


def get_mood_data(from_date: str, to_date: str) -> List:
    return _repo.get_mood_data(from_date, to_date)


def search_journal(query: str) -> List[JournalEntry]:
    return _repo.search(query)


def append_quick_note(text: str) -> JournalEntry:
    """یادداشت سریع (Quick Note) را با برچسب زمانی به انتهای محتوای
    یادداشت روزانه‌ی امروز اضافه می‌کند — بدون بازنویسی چیزی که کاربر
    از قبل در بخش «آزادانه بنویس» نوشته.

    طبق بخش ۶ اسپک: "Quick Note: system‑wide shortcut, floating
    always‑on‑top note, auto‑saved to journal".
    """
    from utils.date_utils import now_iso
    today = today_iso()
    entry = get_or_create_today()
    existing = (entry.content or "").strip()
    timestamp = now_iso()[11:16]  # فقط HH:MM
    new_line = f"[{timestamp}] {text.strip()}"
    combined = f"{existing}\n{new_line}" if existing else new_line
    return save_entry(today, content=combined)


def parse_json_list(json_str: Optional[str]) -> List[str]:
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except Exception:
        return []
