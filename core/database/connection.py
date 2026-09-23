"""
core/database/connection.py
Singleton connection manager با WAL mode و foreign keys.
Thread-safe: هر thread connection مجزا دارد.
"""

import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional
import config

logger = logging.getLogger("life_manager.db")

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """
    Connection thread-local برمی‌گرداند.
    اگر connection برای این thread وجود نداشته باشد، یکی می‌سازد.
    """
    conn: Optional[sqlite3.Connection] = getattr(_local, "conn", None)
    if conn is None:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(config.DB_PATH),
            timeout=config.DB_TIMEOUT,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout = {config.DB_BUSY_TIMEOUT}")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -8000")   # 8 MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        _local.conn = conn
        logger.debug("New DB connection created for thread %s", threading.current_thread().name)
    return conn


def close_connection() -> None:
    conn: Optional[sqlite3.Connection] = getattr(_local, "conn", None)
    if conn:
        conn.close()
        _local.conn = None


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    return get_connection().execute(sql, params)


def executemany(sql: str, params_list) -> sqlite3.Cursor:
    return get_connection().executemany(sql, params_list)


def commit() -> None:
    """Commit روی connection جاری — مگر اینکه در حال حاضر داخل یک
    `with transaction():` باشیم؛ در آن صورت commit واقعی را به
    __exit__ همان transaction واگذار می‌کند تا چند نوشتن پشت‌سرهم
    (چند فراخوانی repository) واقعاً atomic بمانند (یا همه commit
    می‌شوند یا در صورت خطا همه rollback).
    """
    if getattr(_local, "in_transaction", 0) > 0:
        return
    get_connection().commit()


def rollback() -> None:
    get_connection().rollback()


class transaction:
    """Context manager برای گروه‌بندی چند نوشتن (چند فراخوانی
    repository/service) در یک تراکنش atomic واحد.

    نکته‌ی مهم: چون متدهای BaseRepository (_insert/_update/delete) هرکدام
    به‌صورت مستقل commit() صدا می‌زنند، این کلاس یک شمارنده‌ی nesting
    thread-local نگه می‌دارد؛ تا وقتی حداقل یک `transaction` فعال است،
    commit() داخلیِ repository ها عملاً no-op می‌شود و فقط __exit__
    بیرونی‌ترین transaction واقعاً commit/rollback انجام می‌دهد. این
    یعنی کد موجود repository ها بدون هیچ تغییری، به‌صورت خودکار
    atomic-safe می‌شود وقتی داخل `with transaction():` فراخوانی شود.

    مثال (بخش سرویس، نه UI):
        with transaction():
            task_repo.complete(task_id)
            task_repo.create(...)  # spawn نسخه‌ی بعدی تسک تکراری
        # اگر هرکدام خطا بدهد، هر دو rollback می‌شوند.
    """
    def __enter__(self):
        _local.in_transaction = getattr(_local, "in_transaction", 0) + 1
        return get_connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        _local.in_transaction -= 1
        if _local.in_transaction > 0:
            # هنوز داخل یک transaction بیرونی‌تر هستیم؛ commit/rollback
            # واقعی به عهده‌ی آن است.
            return False
        if exc_type:
            rollback()
            logger.error("Transaction rolled back: %s", exc_val)
            return False
        commit()
        return False
