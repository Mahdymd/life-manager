"""core/services/search_service.py — جستجوی سراسری با FTS5.

مطابق بخش ۷.۶ اسپک: "FTS5 index covering all searchable entities.
Unified search interface."

نکته‌ی فنی: هر عبارت جستجو قبل از رفتن به FTS5 escape می‌شود (کوت‌کردن
در دو کوتیشن و دوبرابر کردن کوتیشن داخلی) تا کاراکترهای خاص FTS5 مثل
"، *، NOT، AND (که در MATCH syntax معنی خاص دارند) باعث خطای query یا
رفتار غیرمنتظره نشوند؛ همچنین یک wildcard پیشوندی (*) اضافه می‌شود تا
جستجو در حین تایپ (search-as-you-type) هم کار کند.
"""

from typing import List, Dict
from core.database.connection import get_connection

_MODULE_LABELS = {
    "task": "tasks", "note": "notes", "journal_entry": "journal", "goal": "goals",
}


def _fts_escape(query: str) -> str:
    """عبارت را برای استفاده‌ی امن در FTS5 MATCH آماده می‌کند.

    هر کلمه را در دو کوتیشن قرار می‌دهد (کوتیشن‌های داخلی را دوبرابر
    می‌کند) و با پیشوند wildcard (*) به هم متصل می‌کند — یعنی «جستجوی
    AND پیشوندی روی هر کلمه»، دقیقاً رفتار مطلوب برای یک search-box.
    """
    words = [w for w in query.strip().split() if w]
    if not words:
        return ""
    escaped = []
    for w in words:
        safe = w.replace('"', '""')
        escaped.append(f'"{safe}"*')
    return " AND ".join(escaped)


def global_search(query: str, limit_per_type: int = 5) -> List[Dict]:
    """جستجوی یکپارچه روی tasks/notes/journal/goals با FTS5.

    خروجی: لیستی از دیکشنری‌ها با کلیدهای type/id/title/snippet/module،
    مرتب‌شده بر اساس ارتباط (bm25 rank هر جدول، سپس بر اساس نوع).
    """
    if not query or len(query.strip()) < 2:
        return []

    match_expr = _fts_escape(query)
    if not match_expr:
        return []

    conn = get_connection()
    results: List[Dict] = []

    # ── Tasks ──
    try:
        rows = conn.execute(
            """SELECT t.id, t.title, t.status,
                      snippet(tasks_fts, 1, '[', ']', '…', 8) AS snip
               FROM tasks_fts JOIN tasks t ON t.id = tasks_fts.rowid
               WHERE tasks_fts MATCH ?
               ORDER BY bm25(tasks_fts) LIMIT ?""",
            (match_expr, limit_per_type)).fetchall()
        for r in rows:
            results.append({
                "type": "task", "id": r["id"], "title": r["title"],
                "snippet": r["snip"], "module": "tasks",
            })
    except Exception:
        pass

    # ── Notes ──
    try:
        rows = conn.execute(
            """SELECT n.id, n.title,
                      snippet(notes_fts, 1, '[', ']', '…', 10) AS snip
               FROM notes_fts JOIN notes n ON n.id = notes_fts.rowid
               WHERE notes_fts MATCH ?
               ORDER BY bm25(notes_fts) LIMIT ?""",
            (match_expr, limit_per_type)).fetchall()
        for r in rows:
            results.append({
                "type": "note", "id": r["id"], "title": r["title"],
                "snippet": r["snip"], "module": "notes",
            })
    except Exception:
        pass

    # ── Journal ──
    try:
        rows = conn.execute(
            """SELECT j.id, j.date,
                      snippet(journal_fts, 0, '[', ']', '…', 10) AS snip
               FROM journal_fts JOIN journal_entries j ON j.id = journal_fts.rowid
               WHERE journal_fts MATCH ?
               ORDER BY bm25(journal_fts) LIMIT ?""",
            (match_expr, limit_per_type)).fetchall()
        for r in rows:
            results.append({
                "type": "journal_entry", "id": r["id"], "title": r["date"],
                "snippet": r["snip"], "module": "journal",
            })
    except Exception:
        pass

    # ── Goals ──
    try:
        rows = conn.execute(
            """SELECT g.id, g.title,
                      snippet(goals_fts, 1, '[', ']', '…', 8) AS snip
               FROM goals_fts JOIN goals g ON g.id = goals_fts.rowid
               WHERE goals_fts MATCH ?
               ORDER BY bm25(goals_fts) LIMIT ?""",
            (match_expr, limit_per_type)).fetchall()
        for r in rows:
            results.append({
                "type": "goal", "id": r["id"], "title": r["title"],
                "snippet": r["snip"], "module": "goals",
            })
    except Exception:
        pass

    return results
