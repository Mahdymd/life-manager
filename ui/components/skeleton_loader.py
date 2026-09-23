"""
ui/components/skeleton_loader.py — Skeleton loading placeholder (Phase 4).

طبق بخش ۹ اسپک: "SkeletonLoader" و Definition of Done بخش ۱۶:
"Loading skeleton / async handling (if data‑driven)".

تا الان صفحات در حالت loading (وقتی `BaseViewModel.loading_changed`
سیگنال می‌داد) هیچ نمایش بصری skeleton نداشتند — فقط دکمه‌ها موقتاً
غیرفعال می‌شدند. این کامپوننت آن گپ را می‌بندد.

استفاده‌ی معمول: یک placeholder مستطیلی با انیمیشن shimmer (درخشش
افقی) که در حین بارگذاری به‌جای محتوای واقعی نمایش داده می‌شود.

نکته‌ی accessibility: انیمیشن باید تنظیمات «کاهش حرکت» را رعایت کند
(بخش ۹ اسپک). چون Qt/PySide6 راه قابل‌اتکای cross-platform برای خواندن
مستقیم این تنظیم از سیستم‌عامل ندارد، این ماژول یک override دستی
(`set_reduced_motion`) ارائه می‌دهد تا وقتی چنین گزینه‌ای به تنظیمات
برنامه اضافه شد، از همان‌جا فعال شود.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QLinearGradient

from ui.style.theme_manager import colors, Radius, Motion


_force_reduced_motion = False


def set_reduced_motion(enabled: bool) -> None:
    """کاهش حرکت را برای همه‌ی SkeletonBox های بعدی به‌صورت سراسری
    فعال/غیرفعال می‌کند.

    نکته‌ی صداقت فنی: Qt/PySide6 در این نسخه هیچ API قابل‌اتکای
    cross-platform برای خواندن مستقیم تنظیم «کاهش حرکت» سیستم‌عامل
    ندارد (برخلاف CSS وب که `prefers-reduced-motion` دارد). به همین
    دلیل این تابع یک override دستی است؛ اگر بعداً چنین تنظیمی به
    SettingsRepository اضافه شود (طبق بخش ۹ اسپک)، همان‌جا باید این
    تابع را در startup صدا بزند.
    """
    global _force_reduced_motion
    _force_reduced_motion = enabled


def _reduced_motion() -> bool:
    return _force_reduced_motion


class SkeletonBox(QWidget):
    """یک مستطیل skeleton با انیمیشن shimmer.

    مثال:
        box = SkeletonBox(height=16, radius=Radius.SM)
    """

    def __init__(
        self,
        height: int = 16,
        radius: int = Radius.SM,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._radius = radius
        self._offset = 0.0
        self._reduced = _reduced_motion()

        if not self._reduced:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._advance)
            self._timer.start(30)
        else:
            self._timer = None

    def _advance(self) -> None:
        self._offset = (self._offset + 0.02) % 2.0
        self.update()

    def paintEvent(self, event) -> None:
        c = colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())

        base = QColor(c.surface_elev)
        if self._reduced:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(base)
            painter.drawRoundedRect(rect, self._radius, self._radius)
        else:
            gradient = QLinearGradient(rect.left(), 0, rect.right(), 0)
            pos = self._offset
            gradient.setColorAt(max(0.0, min(1.0, pos - 0.5)) if pos > 0.5 else 0.0, base)
            highlight = QColor(c.border)
            gradient.setColorAt(max(0.0, min(1.0, pos)), highlight)
            gradient.setColorAt(1.0, base)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(rect, self._radius, self._radius)
        painter.end()

    def stop(self) -> None:
        """باید موقع حذف/پنهان‌شدن ویجت صدا زده شود تا تایمر بی‌جهت
        اجرا نماند (بخش ۲۰ اسپک: جلوگیری از leak)."""
        if self._timer:
            self._timer.stop()


class SkeletonLoader(QWidget):
    """چند SkeletonBox پشت‌سرهم — برای شبیه‌سازی چند خط متن یا چند
    ردیف لیست در حین بارگذاری.

    مثال:
        loader = SkeletonLoader(rows=3)
        layout.addWidget(loader)
        # وقتی داده آماده شد:
        loader.hide()
    """

    def __init__(
        self,
        rows: int = 3,
        row_height: int = 16,
        spacing: int = 8,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)
        self._boxes = []
        for _ in range(rows):
            box = SkeletonBox(height=row_height)
            self._boxes.append(box)
            layout.addWidget(box)

    def stop(self) -> None:
        for box in self._boxes:
            box.stop()
