"""core/database/migrations/migration_runner.py — اجرای خودکار migration ها."""

import importlib
import logging
from datetime import datetime
from pathlib import Path
from core.domain.exceptions import MigrationError

logger = logging.getLogger("life_manager.migrations")


def run_migrations() -> None:
    from core.database.connection import get_connection, commit
    conn = get_connection()

    # ایجاد جدول schema_version اگه نباشه
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version     INTEGER PRIMARY KEY,
            applied_at  TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)
    commit()

    mig_dir = Path(__file__).parent
    for f in sorted(mig_dir.glob("v[0-9][0-9][0-9]_*.py")):
        mod_name = f"core.database.migrations.{f.stem}"
        mod = importlib.import_module(mod_name)
        already = conn.execute(
            "SELECT 1 FROM schema_version WHERE version=?", (mod.VERSION,)
        ).fetchone()
        if already:
            continue
        logger.info("Applying migration v%03d: %s", mod.VERSION, mod.DESCRIPTION)
        try:
            mod.up(conn)
            conn.execute(
                "INSERT INTO schema_version(version,applied_at,description) VALUES(?,?,?)",
                (mod.VERSION, datetime.now().isoformat(), mod.DESCRIPTION),
            )
            commit()
            logger.info("Migration v%03d applied.", mod.VERSION)
        except Exception as exc:
            conn.rollback()
            raise MigrationError(mod.VERSION, str(exc)) from exc
