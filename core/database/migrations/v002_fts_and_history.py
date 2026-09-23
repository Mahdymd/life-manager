"""Migration v002 — جستجوی کامل متن (FTS5) و جدول تاریخچه‌ی نسخه‌ها.

مطابق بخش ۷.۶ اسپک: "FTS5 index covering all searchable entities.
Unified search interface."
و بخش ۷.۴: "Version history: maintain a history table for key entities
(tasks, journal) enabling time-travel and undo."

نکات فنی:
- از الگوی استاندارد "external content" FTS5 استفاده شده (نه ذخیره‌ی
  کپی داده در جدول FTS)؛ یعنی خودِ جدول اصلی (tasks/notes/...) تنها
  منبع حقیقت باقی می‌ماند و FTS فقط ایندکس متنی روی آن است — این هم
  حجم دیتابیس رو کمتر نگه می‌داره و هم از ناهم‌خوانی داده جلوگیری می‌کنه.
- سه‌گانه تریگر (AI/AD/AU) بعد از هر insert/update/delete خودکار ایندکس
  FTS رو sync نگه می‌داره؛ سرویس‌ها/repository ها نیازی به تغییر ندارند.
- entity_history فقط برای tasks و journal_entries فعال شده (دقیقاً طبق
  اسپک: "key entities (tasks, journal)")، نه همه‌ی جدول‌ها — تا حجم
  دیتابیس بی‌دلیل رشد نکنه.
"""

VERSION = 2
DESCRIPTION = "افزودن FTS5 برای جستجوی سراسری و جدول entity_history برای time-travel"


def up(conn) -> None:
    # ══════════════════════════════════════════════════════
    #  FTS5 — TASKS
    # ══════════════════════════════════════════════════════
    conn.executescript("""
    CREATE VIRTUAL TABLE IF NOT EXISTS tasks_fts USING fts5(
        title, description,
        content='tasks', content_rowid='id'
    );
    INSERT INTO tasks_fts(rowid, title, description)
        SELECT id, title, COALESCE(description,'') FROM tasks;

    CREATE TRIGGER IF NOT EXISTS tasks_fts_ai AFTER INSERT ON tasks BEGIN
        INSERT INTO tasks_fts(rowid, title, description)
        VALUES (new.id, new.title, COALESCE(new.description,''));
    END;
    CREATE TRIGGER IF NOT EXISTS tasks_fts_ad AFTER DELETE ON tasks BEGIN
        INSERT INTO tasks_fts(tasks_fts, rowid, title, description)
        VALUES ('delete', old.id, old.title, COALESCE(old.description,''));
    END;
    CREATE TRIGGER IF NOT EXISTS tasks_fts_au AFTER UPDATE ON tasks BEGIN
        INSERT INTO tasks_fts(tasks_fts, rowid, title, description)
        VALUES ('delete', old.id, old.title, COALESCE(old.description,''));
        INSERT INTO tasks_fts(rowid, title, description)
        VALUES (new.id, new.title, COALESCE(new.description,''));
    END;
    """)

    # ══════════════════════════════════════════════════════
    #  FTS5 — NOTES
    # ══════════════════════════════════════════════════════
    conn.executescript("""
    CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
        title, content,
        content='notes', content_rowid='id'
    );
    INSERT INTO notes_fts(rowid, title, content)
        SELECT id, title, COALESCE(content,'') FROM notes;

    CREATE TRIGGER IF NOT EXISTS notes_fts_ai AFTER INSERT ON notes BEGIN
        INSERT INTO notes_fts(rowid, title, content)
        VALUES (new.id, new.title, COALESCE(new.content,''));
    END;
    CREATE TRIGGER IF NOT EXISTS notes_fts_ad AFTER DELETE ON notes BEGIN
        INSERT INTO notes_fts(notes_fts, rowid, title, content)
        VALUES ('delete', old.id, old.title, COALESCE(old.content,''));
    END;
    CREATE TRIGGER IF NOT EXISTS notes_fts_au AFTER UPDATE ON notes BEGIN
        INSERT INTO notes_fts(notes_fts, rowid, title, content)
        VALUES ('delete', old.id, old.title, COALESCE(old.content,''));
        INSERT INTO notes_fts(rowid, title, content)
        VALUES (new.id, new.title, COALESCE(new.content,''));
    END;
    """)

    # ══════════════════════════════════════════════════════
    #  FTS5 — JOURNAL ENTRIES
    # ══════════════════════════════════════════════════════
    conn.executescript("""
    CREATE VIRTUAL TABLE IF NOT EXISTS journal_fts USING fts5(
        content, gratitude, wins,
        content='journal_entries', content_rowid='id'
    );
    INSERT INTO journal_fts(rowid, content, gratitude, wins)
        SELECT id, COALESCE(content,''), COALESCE(gratitude,''), COALESCE(wins,'')
        FROM journal_entries;

    CREATE TRIGGER IF NOT EXISTS journal_fts_ai AFTER INSERT ON journal_entries BEGIN
        INSERT INTO journal_fts(rowid, content, gratitude, wins)
        VALUES (new.id, COALESCE(new.content,''), COALESCE(new.gratitude,''), COALESCE(new.wins,''));
    END;
    CREATE TRIGGER IF NOT EXISTS journal_fts_ad AFTER DELETE ON journal_entries BEGIN
        INSERT INTO journal_fts(journal_fts, rowid, content, gratitude, wins)
        VALUES ('delete', old.id, COALESCE(old.content,''), COALESCE(old.gratitude,''), COALESCE(old.wins,''));
    END;
    CREATE TRIGGER IF NOT EXISTS journal_fts_au AFTER UPDATE ON journal_entries BEGIN
        INSERT INTO journal_fts(journal_fts, rowid, content, gratitude, wins)
        VALUES ('delete', old.id, COALESCE(old.content,''), COALESCE(old.gratitude,''), COALESCE(old.wins,''));
        INSERT INTO journal_fts(rowid, content, gratitude, wins)
        VALUES (new.id, COALESCE(new.content,''), COALESCE(new.gratitude,''), COALESCE(new.wins,''));
    END;
    """)

    # ══════════════════════════════════════════════════════
    #  FTS5 — GOALS
    # ══════════════════════════════════════════════════════
    conn.executescript("""
    CREATE VIRTUAL TABLE IF NOT EXISTS goals_fts USING fts5(
        title, description,
        content='goals', content_rowid='id'
    );
    INSERT INTO goals_fts(rowid, title, description)
        SELECT id, title, COALESCE(description,'') FROM goals;

    CREATE TRIGGER IF NOT EXISTS goals_fts_ai AFTER INSERT ON goals BEGIN
        INSERT INTO goals_fts(rowid, title, description)
        VALUES (new.id, new.title, COALESCE(new.description,''));
    END;
    CREATE TRIGGER IF NOT EXISTS goals_fts_ad AFTER DELETE ON goals BEGIN
        INSERT INTO goals_fts(goals_fts, rowid, title, description)
        VALUES ('delete', old.id, old.title, COALESCE(old.description,''));
    END;
    CREATE TRIGGER IF NOT EXISTS goals_fts_au AFTER UPDATE ON goals BEGIN
        INSERT INTO goals_fts(goals_fts, rowid, title, description)
        VALUES ('delete', old.id, old.title, COALESCE(old.description,''));
        INSERT INTO goals_fts(rowid, title, description)
        VALUES (new.id, new.title, COALESCE(new.description,''));
    END;
    """)

    # ══════════════════════════════════════════════════════
    #  ENTITY HISTORY  (فقط tasks و journal_entries — طبق اسپک)
    # ══════════════════════════════════════════════════════
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS entity_history (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type   TEXT    NOT NULL CHECK(entity_type IN ('task','journal_entry')),
        entity_id     INTEGER NOT NULL,
        snapshot_json TEXT    NOT NULL,
        change_type   TEXT    NOT NULL CHECK(change_type IN ('update','delete')),
        changed_at    TEXT    NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_entity_history_lookup
        ON entity_history(entity_type, entity_id, changed_at DESC);
    """)
