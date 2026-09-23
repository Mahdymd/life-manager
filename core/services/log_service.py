"""core/services/log_service.py — صادرکردن لاگ‌ها برای دیباگ (Phase 19).

طبق بخش ۱۹ اسپک: "Provide an 'Export logs' button in settings for
debugging." همه‌ی فایل‌های لاگ (فعلی + rotated backup ها مثل
app.log.1، app.log.2، ...) را در یک فایل zip واحد جمع می‌کند تا کاربر
راحت بتواند برای پشتیبانی بفرستد.
"""

from __future__ import annotations
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List
import config


def list_log_files() -> List[Path]:
    """همه‌ی فایل‌های لاگ موجود (فعلی + rotated) را برمی‌گرداند."""
    if not config.LOG_DIR.exists():
        return []
    return sorted(config.LOG_DIR.glob("app.log*"))


def export_logs(destination_dir: str) -> Path:
    """همه‌ی فایل‌های لاگ را در یک zip در destination_dir ذخیره می‌کند.

    خروجی: مسیر کامل فایل zip ساخته‌شده.
    """
    log_files = list_log_files()
    if not log_files:
        raise FileNotFoundError("هیچ فایل لاگی برای صادرکردن پیدا نشد.")

    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = dest_dir / f"life_manager_logs_{timestamp}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for log_file in log_files:
            zf.write(log_file, arcname=log_file.name)

    return zip_path
