"""tests/conftest.py — Fixture های مشترک pytest.

طبق آیتم High #۳ از Audit: پایه‌ریزی حداقلی pytest (نه پوشش کامل
پروژه). مهم‌ترین چیزی که این فایل تضمین می‌کند: **هیچ تستی هرگز به
دیتابیس واقعی کاربر (config.DB_PATH پیش‌فرض) دست نمی‌زند** — هر تست
یک فایل SQLite کاملاً موقت و ایزوله می‌گیرد که migration های واقعی
پروژه رویش اجرا شده‌اند.
"""

import sys
from pathlib import Path

import pytest

# تضمین می‌کند `import config` و `from core...`/`from ui...` مستقل
# از اینکه pytest از کدام دایرکتوری اجرا شده کار کنند (بدون نیاز به
# نصب پکیج یا PYTHONPATH دستی).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    """یک دیتابیس SQLite تازه و موقت برای این تست به‌تنهایی.

    - config.DATA_DIR/config.DB_PATH موقتاً به یک مسیر temp اشاره
      می‌کنند (monkeypatch خودش بعد از تست برمی‌گرداند).
    - اتصال thread-local قبلی (اگر از تست دیگری یا import باقی مانده)
      قبل و بعد از تست بسته می‌شود تا نشتی بین تست‌ها رخ ندهد.
    - migration های واقعی پروژه (core/database/migrations) روی این
      دیتابیس اجرا می‌شوند، دقیقاً همان چیزی که main.py هنگام
      استارتاپ واقعی اجرا می‌کند — یعنی تست‌ها روی همان schema واقعی
      کار می‌کنند، نه یک mock جداگانه.
    """
    import config
    from core.database.connection import close_connection

    close_connection()
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test_life_manager.db")

    from core.database.migrations.migration_runner import run_migrations
    run_migrations()

    yield config.DB_PATH

    close_connection()
