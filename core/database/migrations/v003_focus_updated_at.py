"""Migration v003 — ستون updated_at برای focus_sessions.

BaseRepository._insert/_update همیشه updated_at می‌نویسد. جدول
focus_sessions در v001 این ستون را نداشت، بنابراین start_session با
sqlite3.OperationalError شکست می‌خورد و آمار پومودورو همیشه صفر می‌ماند.
"""

VERSION = 3
DESCRIPTION = "افزودن updated_at به focus_sessions برای سازگاری با BaseRepository"


def up(conn) -> None:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(focus_sessions)").fetchall()]
    if "updated_at" in cols:
        return
    conn.execute("ALTER TABLE focus_sessions ADD COLUMN updated_at TEXT")
    conn.execute(
        "UPDATE focus_sessions SET updated_at = created_at WHERE updated_at IS NULL"
    )
