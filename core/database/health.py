"""
core/database/health.py — بررسی سلامت پایگاه‌داده و بازیابی خودکار.

مطابق بخش ۷.۱ اسپک:
"Auto-run PRAGMA integrity_check at startup; if fails, attempt repair
from backup."

این ماژول دو مسئولیت دارد:
1. check_integrity(): اجرای PRAGMA integrity_check (سریع، در startup).
2. attempt_repair_from_backup(): اگر integrity_check شکست خورد، جدیدترین
   بکاپ معتبر را پیدا کرده و بازیابی می‌کند (با نگه‌داشتن نسخه‌ی خراب
   برای بررسی دستی بعدی — restore_backup در backup_service از قبل این
   کار را می‌کند: قبل از overwrite یک کپی از DB فعلی می‌گیرد).
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional
from core.database.connection import get_connection, close_connection

logger = logging.getLogger("life_manager.db.health")


@dataclass
class IntegrityResult:
    ok: bool
    detail: str  # "ok" یا خروجی خام PRAGMA integrity_check (لیست خطاها)


def check_integrity(quick: bool = False) -> IntegrityResult:
    """
    اجرای PRAGMA integrity_check (یا quick_check برای بررسی سریع‌تر و
    سبک‌تر — طبق بخش ۱۷ اسپک: "run_migrations... quick integrity check"
    در startup باید سریع باشد).

    quick=True → از PRAGMA quick_check استفاده می‌کند (ساختار صفحات را
    بررسی می‌کند، سریع‌تر از integrity_check کامل که تمام ایندکس‌ها و
    foreign key ها را هم چک می‌کند).
    """
    conn = get_connection()
    pragma = "quick_check" if quick else "integrity_check"
    try:
        rows = conn.execute(f"PRAGMA {pragma}").fetchall()
    except Exception as exc:
        logger.error("Integrity check failed to execute: %s", exc)
        return IntegrityResult(ok=False, detail=str(exc))

    if len(rows) == 1 and rows[0][0] == "ok":
        return IntegrityResult(ok=True, detail="ok")

    detail = "; ".join(r[0] for r in rows) if rows else "unknown error"
    logger.critical("Database integrity check FAILED: %s", detail)
    return IntegrityResult(ok=False, detail=detail)


def attempt_repair_from_backup() -> bool:
    """
    اگر integrity_check شکست بخورد، این تابع تلاش می‌کند جدیدترین بکاپ
    معتبر (روزانه/هفتگی/ماهانه/دستی) را پیدا کرده و بازیابی کند.

    نکته‌ی امنیت داده: restore_backup در backup_service.py قبل از
    جایگزینی، یک کپی از DB فعلی (خراب) را با پیشوند
    "life_manager_before_restore_..." نگه می‌دارد — پس هیچ داده‌ای
    برای همیشه از دست نمی‌رود، فقط کنار گذاشته می‌شود.

    خروجی: True اگر بازیابی انجام شد و integrity_check بعد از آن پاس شد.
    """
    from core.services.backup_service import list_backups, restore_backup

    try:
        backups = list_backups()
    except Exception as exc:
        logger.error("Cannot list backups for repair: %s", exc)
        return False

    if not backups:
        logger.error("No backups available for automatic repair.")
        return False

    # جدیدترین بکاپ بر اساس created_at (فارغ از نوع: روزانه/هفتگی/...)
    backups_sorted = sorted(
        backups, key=lambda b: b.get("created_at") or "", reverse=True
    )
    latest = backups_sorted[0]

    logger.warning("Attempting automatic repair from backup: %s", latest["name"])
    try:
        restore_backup(latest["path"])
    except Exception as exc:
        logger.critical("Automatic repair failed: %s", exc)
        return False

    # اتصال قبلی به فایل خراب اشاره می‌کرد؛ باید بسته و از نو باز شود
    close_connection()
    result = check_integrity()
    if result.ok:
        logger.info("Automatic repair succeeded; database restored from %s", latest["name"])
        return True
    logger.critical("Database still corrupt after restore attempt.")
    return False


def run_startup_check(quick: bool = True) -> Optional[str]:
    """
    نقطه‌ی ورود startup (فراخوانی از main.py/run.py، طبق ترتیب بخش ۱۷:
    "Open database and validate (integrity_check quick)").

    خروجی: None اگر سالم بود (یا با موفقیت ترمیم شد)، یا یک پیام خطای
    فارسی قابل‌نمایش به کاربر اگر ترمیم هم شکست خورد (در این حالت برنامه
    باید با هشدار صریح ادامه پیدا کند یا کاربر را مطلع کند، نه اینکه
    بی‌سروصدا روی داده‌ی خراب کار کند).
    """
    result = check_integrity(quick=quick)
    if result.ok:
        return None

    logger.critical("Startup integrity check failed: %s", result.detail)
    repaired = attempt_repair_from_backup()
    if repaired:
        return None

    return (
        "پایگاه‌داده آسیب دیده و بازیابی خودکار از بکاپ ناموفق بود. "
        "فایل دیتابیس فعلی حفظ شده؛ لطفاً از منوی تنظیمات یک بکاپ قدیمی‌تر "
        "را به‌صورت دستی بازیابی کنید یا با پشتیبانی تماس بگیرید."
    )
