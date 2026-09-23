"""core/services/session_service.py — تشخیص خروج ناگهانی (Crash Detection).

مطابق بخش ۷.۴ اسپک: "Crash recovery: on unexpected shutdown, restore
previous session and recover unsaved data from WAL or backup, notify
user." و بخش ۱۸ (Session Recovery).

مکانیزم: یک فایل نشانه (flag file) به نام ".running" داخل DATA_DIR
نوشته می‌شود درست بعد از آماده‌شدن دیتابیس در ابتدای اجرا، و در
closeEvent (خروج تمیز) حذف می‌شود.

اگر در startup بعدی این فایل از قبل وجود داشته باشد، یعنی دفعه‌ی قبل
برنامه به‌طور تمیز بسته نشده (crash، قطع برق، kill شدن پردازه، و...).

نکته: چون SQLite با WAL mode کار می‌کند، خودِ داده معمولاً حتی بعد از
crash هم safe است (WAL خودش را در باز شدن بعدی connection، replay
می‌کند) — این فایل صرفاً برای «اطلاع‌رسانی شفاف به کاربر» است، نه یک
مکانیزم بازیابی داده به‌تنهایی.
"""

from __future__ import annotations
import logging
from pathlib import Path
import config

logger = logging.getLogger("life_manager.session")

_FLAG_NAME = ".running"


def _flag_path() -> Path:
    return config.DATA_DIR / _FLAG_NAME


def was_previous_session_clean() -> bool:
    """اگر فایل نشانه از اجرای قبلی باقی مانده باشد (یعنی dirty exit)، False برمی‌گرداند.
    باید فقط یک‌بار، در همان ابتدای startup و قبل از mark_running_now()
    فراخوانی شود."""
    return not _flag_path().exists()


def mark_running_now() -> None:
    """باید بلافاصله بعد از آماده‌شدن دیتابیس (و بعد از چک
    was_previous_session_clean) فراخوانی شود."""
    try:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        _flag_path().write_text("1", encoding="utf-8")
    except Exception:
        logger.warning("Could not write session running-flag.", exc_info=True)


def mark_clean_exit() -> None:
    """باید در closeEvent (خروج تمیز از برنامه) فراخوانی شود."""
    try:
        _flag_path().unlink(missing_ok=True)
    except Exception:
        logger.warning("Could not clear session running-flag.", exc_info=True)
