"""
ui/viewmodels/settings_viewmodel.py

ViewModel صفحه‌ی تنظیمات. الگو از task_list_viewmodel.py.

نکته: عملیات این صفحه (بکاپ‌گیری، بازیابی، حذف کامل داده‌ها، شمارش
رکوردهای ۱۱ جدول) می‌توانند به‌طور محسوسی کند باشند (I/O فایل یا اسکن
چند جدول)؛ همه از طریق run_async روی Worker اجرا می‌شوند تا هرگز UI
thread را قفل نکنند — این دقیقاً همان چیزی است که فاز ۳ می‌خواست رفع کند.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.services.backup_service import (
    manual_backup, list_backups, restore_backup,
    get_db_stats_text, reset_all_user_data,
)
import config


def _fetch_settings() -> Dict:
    from core.repositories.settings_repository import SettingsRepository
    s = SettingsRepository()
    return {
        "theme": s.get("theme", "dark"),
        "accent_color": s.get("accent_color", "") or None,
        "reduced_motion": s.get_bool("reduced_motion", False),
        "currency_symbol": s.get("currency_symbol", "تومان"),
        "pomodoro_work_min": s.get_int("pomodoro_work_min", config.POMODORO_WORK_MIN),
        "pomodoro_short_break": s.get_int("pomodoro_short_break", config.POMODORO_SHORT_BREAK),
        "pomodoro_long_break": s.get_int("pomodoro_long_break", config.POMODORO_LONG_BREAK),
        "pomodoro_long_after": s.get_int("pomodoro_long_after", config.POMODORO_LONG_AFTER),
    }


def _save_general(theme: str, currency_symbol: str) -> None:
    from core.repositories.settings_repository import SettingsRepository
    s = SettingsRepository()
    s.set("theme", theme)
    s.set("currency_symbol", currency_symbol)


def _save_reduced_motion(enabled: bool) -> None:
    from core.repositories.settings_repository import SettingsRepository
    SettingsRepository().set("reduced_motion", "1" if enabled else "0")


def _save_pomodoro(work: int, short_break: int, long_break: int, long_after: int) -> None:
    from core.repositories.settings_repository import SettingsRepository
    s = SettingsRepository()
    s.set("pomodoro_work_min", str(work))
    s.set("pomodoro_short_break", str(short_break))
    s.set("pomodoro_long_break", str(long_break))
    s.set("pomodoro_long_after", str(long_after))


def _fetch_db_stats() -> str:
    return get_db_stats_text()


def _reset_all_data() -> None:
    """Safety backup then wipe user tables — delegated to backup_service."""
    reset_all_user_data()


class SettingsViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی تنظیمات.

    Signals:
        settings_loaded(dict)
        db_stats_loaded(str)
        backups_loaded(list)
        backup_created(str): نام فایل بکاپ تازه‌ساخته‌شده (برای Toast).
        restore_completed()
        reset_completed()
    """

    settings_loaded = Signal(dict)
    db_stats_loaded = Signal(str)
    backups_loaded = Signal(list)
    backup_created = Signal(str)
    restore_completed = Signal()
    reset_completed = Signal()
    logs_exported = Signal(str)

    def load_settings(self) -> None:
        self.run_async(_fetch_settings, self.settings_loaded.emit)

    def load_db_stats(self) -> None:
        self.run_async(_fetch_db_stats, self.db_stats_loaded.emit)

    def load_backups(self) -> None:
        self.run_async(list_backups, self.backups_loaded.emit)

    def save_general(self, theme: str, currency_symbol: str) -> None:
        self.run_async(_save_general, lambda _r: None, theme, currency_symbol)

    def save_reduced_motion(self, enabled: bool) -> None:
        self.run_async(_save_reduced_motion, lambda _r: None, enabled)

    def save_pomodoro(self, work: int, short_break: int, long_break: int, long_after: int) -> None:
        self.run_async(_save_pomodoro, lambda _r: None, work, short_break, long_break, long_after)

    def create_manual_backup(self) -> None:
        self.run_async(manual_backup, self._on_backup_created)

    def _on_backup_created(self, path: Path) -> None:
        self.backup_created.emit(path.name)
        self.load_backups()

    def restore(self, path) -> None:
        self.run_async(restore_backup, lambda _r: self.restore_completed.emit(), path)

    def reset_all_data(self) -> None:
        self.run_async(_reset_all_data, lambda _r: self.reset_completed.emit())

    def export_logs(self, destination_dir: str) -> None:
        """طبق بخش ۱۹ اسپک: "Provide an 'Export logs' button in
        settings for debugging"."""
        from core.services.log_service import export_logs as _export_logs
        self.run_async(
            _export_logs,
            lambda zip_path: self.logs_exported.emit(str(zip_path)),
            destination_dir,
        )
