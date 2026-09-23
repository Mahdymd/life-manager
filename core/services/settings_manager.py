"""core/services/settings_manager.py — دسترسی متمرکز به QSettings.

طبق بخش ۱۳ اسپک: "Configuration System: All settings centralized in
SettingsManager (using QSettings). No scattered settings across the
codebase."

قبل از این ماژول، ``QSettings("LifeManager", "LifeManager")`` مستقیماً
در سه فایل جدا (``ui/main_window.py``, ``ui/pages/dashboard_page.py``,
``ui/components/command_palette.py``) صدا زده می‌شد. این کلاس همان
organization/application name را حفظ می‌کند (تا تنظیمات ذخیره‌شده‌ی
کاربران فعلی هنگام آپدیت از دست نرود) و یک singleton واحد ارائه
می‌دهد — دقیقاً همان الگوی ``ui/style/theme_manager.py:get_theme_manager()``.

نکته‌ی مهم: این کلاس مکمل ``SettingsRepository``
(``core/repositories/settings_repository.py``) است، نه جایگزین آن؛
``SettingsRepository`` تنظیمات سطح-اپلیکیشن را در دیتابیس نگه می‌دارد
(theme, last_module, onboarding_completed, پومودورو و...) و برای
همه‌ی این‌ها همان جای درست باقی می‌ماند (این جابه‌جایی هم عمداً انجام
نشد چون تغییر معماری غیرضروری است). ``SettingsManager`` فقط مسئول
تنظیماتی است که ذاتاً به QSettings (per-machine، نه per-user-data)
تعلق دارند: هندسه‌ی پنجره (``QByteArray``)، چیدمان dashboard، و
جستجوهای اخیر Command Palette — همان سه محلی که قبلاً پراکنده بودند.

استفاده:
    from core.services.settings_manager import get_settings_manager
    sm = get_settings_manager()
    sm.set_window_geometry(self.saveGeometry())
"""

from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import QSettings, QByteArray

_ORG = "LifeManager"
_APP = "LifeManager"


class SettingsManager:
    """رَپِر متمرکز روی QSettings — تمام کلیدهای شناخته‌شده اینجا
    تعریف شده‌اند تا هیچ‌جای دیگری از کد مستقیماً QSettings را صدا
    نزند و کلیدها در چند فایل تکرار/فراموش نشوند."""

    def __init__(self) -> None:
        self._settings = QSettings(_ORG, _APP)

    # ── Window geometry (ui/main_window.py) ──────────────────
    def window_geometry(self) -> Optional[QByteArray]:
        return self._settings.value("geometry")

    def set_window_geometry(self, geometry: QByteArray) -> None:
        self._settings.setValue("geometry", geometry)

    # ── Dashboard widget order (ui/pages/dashboard_page.py) ──
    def dashboard_widget_order(self) -> Optional[list]:
        saved = self._settings.value("dashboard/widget_order")
        return saved if isinstance(saved, list) else None

    def set_dashboard_widget_order(self, order: List[str]) -> None:
        self._settings.setValue("dashboard/widget_order", order)

    # ── Command palette recent searches (ui/components/command_palette.py) ──
    def recent_searches(self, limit: int = 8) -> List[str]:
        saved = self._settings.value("command_palette/recent_searches")
        if saved and isinstance(saved, list):
            return [str(s) for s in saved][:limit]
        return []

    def set_recent_searches(self, searches: List[str]) -> None:
        self._settings.setValue("command_palette/recent_searches", searches)

    def sync(self) -> None:
        """فلاش فوری تنظیمات روی دیسک (مثلاً درست قبل از بستن برنامه،
        جایی که نمی‌شود منتظر flush خودکار Qt در پس‌زمینه ماند)."""
        self._settings.sync()


_instance: Optional["SettingsManager"] = None


def get_settings_manager() -> "SettingsManager":
    """Singleton accessor — دقیقاً همان الگوی get_theme_manager()."""
    global _instance
    if _instance is None:
        _instance = SettingsManager()
    return _instance
