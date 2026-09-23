"""ui/components/avatar.py — آواتار دایره‌ای (Phase 4).

طبق بخش ۹ اسپک: "Avatar". از آنجا که این برنامه پروفایل کاربری با
عکس ندارد (تک‌کاربره و آفلاین است)، این کامپوننت بیشتر برای نمایش
حروف اول یک نام (مثلاً در سرصفحه یا لیست مخاطبین آینده) کاربرد دارد؛
اما در صورت وجود مسیر فایل تصویر هم پشتیبانی می‌کند.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPixmap, QFont, QPainterPath

from ui.style.theme_manager import colors


class Avatar(QWidget):
    """آواتار دایره‌ای — یا تصویر (image_path) یا حروف اول یک نام.

    مثال:
        Avatar(name="مهدی رضایی")          # → "م ر" داخل دایره
        Avatar(image_path="user.png")       # → عکس دایره‌ای‌شده
    """

    def __init__(
        self,
        name: str = "",
        image_path: Optional[str] = None,
        size: int = 40,
        accent: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._name = name
        self._image_path = image_path
        self._accent = accent
        self.setFixedSize(size, size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _initials(self) -> str:
        parts = [p for p in self._name.strip().split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][0].upper()
        return (parts[0][0] + parts[1][0]).upper()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())

        if self._image_path:
            pixmap = QPixmap(self._image_path)
            if not pixmap.isNull():
                path = QPainterPath()
                path.addEllipse(rect)
                painter.setClipPath(path)
                scaled = pixmap.scaled(
                    self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                return

        c = colors()
        bg = QColor(self._accent or c.primary)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawEllipse(rect)

        painter.setPen(QColor(c.primary_text))
        font = QFont()
        font.setPointSize(max(9, self.width() // 3))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._initials())
        painter.end()
