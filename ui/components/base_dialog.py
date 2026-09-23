"""ui/components/base_dialog.py — دیالوگ پایه‌ی برنامه (Phase 4، آخرین کامپوننت).

طبق بخش ۹ اسپک: "Dialog, Drawer (custom overlay)" — Drawer در
drawer.py ساخته شد؛ این فایل نیمه‌ی دیگر (Dialog) را کامل می‌کند.

نکته‌ی مهم (یافته‌ی جانبی حین ساخت): ظاهر پایه‌ی QDialog (رنگ پس‌زمینه،
border، border-radius) از قبل به‌صورت سراسری در ThemeManager تعریف شده
بود؛ اما چند دیالوگ (مثل TaskFormDialog) همان استایل را عیناً دوباره
inline تکرار کرده بودند (کد مرده‌ی تکراری — طبق قانون «no duplication»
در بخش ۱۵ اسپک، حذف شد). BaseDialog این تکرار را برای دیالوگ‌های آینده
اساساً غیرممکن می‌کند، چون همه‌ی boilerplate اینجاست.

به‌روزرسانی (Phase 9): طبق بخش ۹ اسپک "Modals fade in with backdrop
blur" — QDialog به‌صورت پنجره‌ی top-level جدا نمایش داده می‌شود (نه
فرزند embedded در layout والد)، پس یک backdrop واقعی نیاز به یک ویجت
نیمه‌شفاف جدا روی پنجره‌ی والد دارد؛ این کلاس آن را به‌صورت خودکار
مدیریت می‌کند (ساخت قبل از exec، حذف بعد از exec). Qt Widgets بلور
واقعی (Gaussian blur پشت‌صحنه) ندارد؛ نزدیک‌ترین معادل قابل‌اتکا یک
overlay نیمه‌شفاف تیره است (همان تکنیک OnboardingOverlay).
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve

from ui.style.theme_manager import Spacing, Motion


class _DialogBackdrop(QWidget):
    """پس‌زمینه‌ی نیمه‌شفاف پشت دیالوگ — روی پنجره‌ی والد نمایش داده می‌شود."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 110);")
        self.setGeometry(parent.rect())
        self.show()
        self.raise_()


class BaseDialog(QDialog):
    """پایه‌ی مشترک همه‌ی دیالوگ‌های فرم برنامه.

    ظاهر (رنگ/border/radius) از QSS سراسری می‌آید — اینجا فقط رفتار
    مشترک (modal بودن، حداقل عرض، margin استاندارد بدنه، backdrop و
    fade-in) تنظیم می‌شود.

    مثال:
        class MyFormDialog(BaseDialog):
            def __init__(self, parent=None):
                super().__init__("عنوان دیالوگ", parent, min_width=480)
                self.body.addWidget(QLabel("محتوا..."))
    """

    def __init__(
        self,
        title: str = "",
        parent: Optional[QWidget] = None,
        min_width: int = 420,
    ) -> None:
        super().__init__(parent)
        if title:
            self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setMinimumWidth(min_width)

        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(Spacing.XXL + 4, Spacing.XL, Spacing.XXL + 4, Spacing.XL)
        self.body.setSpacing(Spacing.LG)

        self._backdrop: Optional[_DialogBackdrop] = None
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(Motion.FAST)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def exec(self):
        """قبل از نمایش، اگر پنجره‌ی والدی وجود داشته باشد، backdrop
        نیمه‌شفاف پشت دیالوگ نمایش داده می‌شود؛ بعد از بسته‌شدن دیالوگ
        (هر نتیجه‌ای)، backdrop حذف می‌شود."""
        host = self.parent().window() if self.parent() else None
        if host is not None:
            self._backdrop = _DialogBackdrop(host)
        self._fade_anim.start()
        try:
            return super().exec()
        finally:
            if self._backdrop is not None:
                self._backdrop.deleteLater()
                self._backdrop = None
