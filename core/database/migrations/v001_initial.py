"""Migration v001 — طرح اولیه کامل دیتابیس."""

VERSION = 1
DESCRIPTION = "ایجاد طرح اولیه کامل دیتابیس"


def up(conn) -> None:
    conn.executescript("""
    -- ═══════════════ CORE ═══════════════
    CREATE TABLE IF NOT EXISTS schema_version (
        version     INTEGER PRIMARY KEY,
        applied_at  TEXT    NOT NULL,
        description TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tags (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL UNIQUE,
        color       TEXT    DEFAULT '#6366f1',
        created_at  TEXT    NOT NULL,
        updated_at  TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS taggables (
        tag_id      INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
        entity_type TEXT    NOT NULL,
        entity_id   INTEGER NOT NULL,
        PRIMARY KEY (tag_id, entity_type, entity_id)
    );

    CREATE TABLE IF NOT EXISTS categories (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        module      TEXT    NOT NULL,
        name        TEXT    NOT NULL,
        color       TEXT,
        icon        TEXT,
        sort_order  INTEGER DEFAULT 0,
        created_at  TEXT    NOT NULL,
        UNIQUE(module, name)
    );

    -- ═══════════════ GOALS ═══════════════
    CREATE TABLE IF NOT EXISTS goals (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        title            TEXT    NOT NULL,
        description      TEXT,
        horizon          TEXT    NOT NULL CHECK(horizon IN ('vision','annual','quarterly')),
        category_id      INTEGER REFERENCES categories(id) ON DELETE SET NULL,
        parent_goal_id   INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        start_date       TEXT,
        target_date      TEXT,
        status           TEXT    DEFAULT 'active'
                         CHECK(status IN ('active','done','paused','cancelled')),
        progress_mode    TEXT    DEFAULT 'auto'
                         CHECK(progress_mode IN ('auto','manual')),
        manual_progress  REAL    DEFAULT 0 CHECK(manual_progress BETWEEN 0 AND 100),
        sort_order       INTEGER DEFAULT 0,
        created_at       TEXT    NOT NULL,
        updated_at       TEXT    NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_goals_status  ON goals(status);
    CREATE INDEX IF NOT EXISTS idx_goals_horizon ON goals(horizon);
    CREATE INDEX IF NOT EXISTS idx_goals_parent  ON goals(parent_goal_id);

    CREATE TABLE IF NOT EXISTS goal_key_results (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id    INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
        title      TEXT    NOT NULL,
        target     REAL    NOT NULL,
        current    REAL    DEFAULT 0,
        unit       TEXT,
        created_at TEXT    NOT NULL,
        updated_at TEXT    NOT NULL
    );

    -- ═══════════════ PROJECTS & TASKS ═══════════════
    CREATE TABLE IF NOT EXISTS projects (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT    NOT NULL,
        description TEXT,
        goal_id     INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
        status      TEXT    DEFAULT 'active'
                    CHECK(status IN ('active','done','archived')),
        color       TEXT    DEFAULT '#6366f1',
        sort_order  INTEGER DEFAULT 0,
        created_at  TEXT    NOT NULL,
        updated_at  TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        title          TEXT    NOT NULL,
        description    TEXT,
        project_id     INTEGER REFERENCES projects(id) ON DELETE SET NULL,
        goal_id        INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        parent_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
        category_id    INTEGER REFERENCES categories(id) ON DELETE SET NULL,
        due_date       TEXT,
        due_time       TEXT,
        priority       TEXT    DEFAULT 'medium'
                       CHECK(priority IN ('urgent','high','medium','low')),
        status         TEXT    DEFAULT 'todo'
                       CHECK(status IN ('todo','in_progress','done','cancelled')),
        estimated_min  INTEGER,
        actual_min     INTEGER,
        recurrence     TEXT    DEFAULT 'none'
                       CHECK(recurrence IN ('none','daily','weekly','monthly','custom')),
        recur_config   TEXT,
        completed_at   TEXT,
        sort_order     INTEGER DEFAULT 0,
        created_at     TEXT    NOT NULL,
        updated_at     TEXT    NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_tasks_status     ON tasks(status);
    CREATE INDEX IF NOT EXISTS idx_tasks_due_date   ON tasks(due_date);
    CREATE INDEX IF NOT EXISTS idx_tasks_project    ON tasks(project_id);
    CREATE INDEX IF NOT EXISTS idx_tasks_goal       ON tasks(goal_id);
    CREATE INDEX IF NOT EXISTS idx_tasks_parent     ON tasks(parent_task_id);

    -- ═══════════════ HABITS ═══════════════
    CREATE TABLE IF NOT EXISTS habits (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT    NOT NULL,
        description  TEXT,
        goal_id      INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        category     TEXT,
        frequency    TEXT    DEFAULT 'daily'
                     CHECK(frequency IN ('daily','weekly','custom')),
        target_days  TEXT,
        target_count INTEGER DEFAULT 1,
        color        TEXT    DEFAULT '#22c55e',
        icon         TEXT    DEFAULT '⭐',
        archived     INTEGER DEFAULT 0,
        sort_order   INTEGER DEFAULT 0,
        created_at   TEXT    NOT NULL,
        updated_at   TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS habit_logs (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id   INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
        date       TEXT    NOT NULL,
        count      INTEGER DEFAULT 1,
        note       TEXT,
        created_at TEXT    NOT NULL,
        UNIQUE(habit_id, date)
    );
    CREATE INDEX IF NOT EXISTS idx_habit_logs ON habit_logs(habit_id, date);

    -- ═══════════════ FINANCE ═══════════════
    CREATE TABLE IF NOT EXISTS transactions (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        type         TEXT    NOT NULL CHECK(type IN ('income','expense','transfer')),
        amount       REAL    NOT NULL CHECK(amount > 0),
        category_id  INTEGER REFERENCES categories(id) ON DELETE SET NULL,
        date         TEXT    NOT NULL,
        note         TEXT,
        goal_id      INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        is_recurring INTEGER DEFAULT 0,
        recur_config TEXT,
        created_at   TEXT    NOT NULL,
        updated_at   TEXT    NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date);
    CREATE INDEX IF NOT EXISTS idx_tx_type ON transactions(type);

    CREATE TABLE IF NOT EXISTS budgets (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id   INTEGER NOT NULL UNIQUE REFERENCES categories(id) ON DELETE CASCADE,
        monthly_limit REAL    NOT NULL CHECK(monthly_limit > 0),
        alert_at_pct  INTEGER DEFAULT 80,
        created_at    TEXT    NOT NULL,
        updated_at    TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS saving_goals (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        title          TEXT    NOT NULL,
        target_amount  REAL    NOT NULL,
        current_amount REAL    DEFAULT 0,
        target_date    TEXT,
        goal_id        INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        status         TEXT    DEFAULT 'active'
                       CHECK(status IN ('active','done','cancelled')),
        created_at     TEXT    NOT NULL,
        updated_at     TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS assets (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT    NOT NULL,
        type       TEXT    NOT NULL,
        value      REAL    NOT NULL,
        date       TEXT    NOT NULL,
        note       TEXT,
        created_at TEXT    NOT NULL,
        updated_at TEXT    NOT NULL
    );

    -- ═══════════════ JOURNAL ═══════════════
    CREATE TABLE IF NOT EXISTS journal_entries (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        date       TEXT    NOT NULL UNIQUE,
        content    TEXT,
        mood       INTEGER CHECK(mood BETWEEN 1 AND 5),
        energy     INTEGER CHECK(energy BETWEEN 1 AND 5),
        gratitude  TEXT,
        wins       TEXT,
        created_at TEXT    NOT NULL,
        updated_at TEXT    NOT NULL
    );

    -- ═══════════════ NOTES ═══════════════
    CREATE TABLE IF NOT EXISTS notes (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        title      TEXT    NOT NULL,
        content    TEXT,
        parent_id  INTEGER REFERENCES notes(id) ON DELETE SET NULL,
        is_pinned  INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        created_at TEXT    NOT NULL,
        updated_at TEXT    NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_notes_parent ON notes(parent_id);

    CREATE TABLE IF NOT EXISTS note_links (
        source_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
        target_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
        PRIMARY KEY(source_note_id, target_note_id)
    );

    -- ═══════════════ FOCUS ═══════════════
    CREATE TABLE IF NOT EXISTS focus_sessions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id     INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
        type        TEXT    DEFAULT 'pomodoro'
                    CHECK(type IN ('pomodoro','short_break','long_break','custom')),
        planned_min INTEGER NOT NULL,
        actual_min  INTEGER,
        status      TEXT    DEFAULT 'completed'
                    CHECK(status IN ('completed','interrupted','skipped')),
        started_at  TEXT    NOT NULL,
        ended_at    TEXT,
        note        TEXT,
        created_at  TEXT    NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_focus_started ON focus_sessions(started_at);

    -- ═══════════════ HEALTH ═══════════════
    CREATE TABLE IF NOT EXISTS health_metrics (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        date       TEXT    NOT NULL,
        type       TEXT    NOT NULL,
        value      REAL    NOT NULL,
        note       TEXT,
        created_at TEXT    NOT NULL,
        UNIQUE(date, type)
    );
    CREATE INDEX IF NOT EXISTS idx_health_date ON health_metrics(date, type);

    CREATE TABLE IF NOT EXISTS workouts (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        date         TEXT    NOT NULL,
        type         TEXT    NOT NULL,
        duration_min INTEGER,
        calories     INTEGER,
        note         TEXT,
        created_at   TEXT    NOT NULL,
        updated_at   TEXT    NOT NULL
    );

    -- ═══════════════ LEARNING ═══════════════
    CREATE TABLE IF NOT EXISTS books (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT    NOT NULL,
        author       TEXT,
        category     TEXT,
        status       TEXT    DEFAULT 'want'
                     CHECK(status IN ('want','reading','done','abandoned')),
        total_pages  INTEGER,
        current_page INTEGER DEFAULT 0,
        rating       INTEGER CHECK(rating BETWEEN 1 AND 5),
        notes        TEXT,
        started_at   TEXT,
        finished_at  TEXT,
        goal_id      INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        created_at   TEXT    NOT NULL,
        updated_at   TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS courses (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        title         TEXT    NOT NULL,
        platform      TEXT,
        category      TEXT,
        status        TEXT    DEFAULT 'want'
                      CHECK(status IN ('want','in_progress','done','abandoned')),
        total_lessons INTEGER,
        done_lessons  INTEGER DEFAULT 0,
        rating        INTEGER CHECK(rating BETWEEN 1 AND 5),
        notes         TEXT,
        goal_id       INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        created_at    TEXT    NOT NULL,
        updated_at    TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS skills (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT    NOT NULL,
        category     TEXT,
        level        INTEGER DEFAULT 1 CHECK(level BETWEEN 1 AND 5),
        target_level INTEGER DEFAULT 5,
        note         TEXT,
        goal_id      INTEGER REFERENCES goals(id) ON DELETE SET NULL,
        created_at   TEXT    NOT NULL,
        updated_at   TEXT    NOT NULL
    );

    -- ═══════════════ CALENDAR ═══════════════
    CREATE TABLE IF NOT EXISTS events (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT    NOT NULL,
        description  TEXT,
        date         TEXT    NOT NULL,
        time         TEXT,
        end_date     TEXT,
        end_time     TEXT,
        is_all_day   INTEGER DEFAULT 1,
        type         TEXT    DEFAULT 'personal'
                     CHECK(type IN ('personal','birthday','anniversary','reminder')),
        recurrence   TEXT    DEFAULT 'none',
        recur_config TEXT,
        color        TEXT    DEFAULT '#6366f1',
        created_at   TEXT    NOT NULL,
        updated_at   TEXT    NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);

    -- ═══════════════ SETTINGS ═══════════════
    CREATE TABLE IF NOT EXISTS app_settings (
        key        TEXT PRIMARY KEY,
        value      TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)


def down(conn) -> None:
    pass  # در production از down استفاده نمی‌کنیم
