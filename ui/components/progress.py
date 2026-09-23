"""
ui/components/progress.py — BaseProgressBar و CircularProgress (Phase 4).

طبق بخش ۹ اسپک: "ProgressBar, CircularProgress".

BaseProgressBar دقیقاً همان الگوی QSS تکراری را جمع می‌کند که در
finance_page.py، goals_page.py، analytics_page.py و habits_page.py با
کمی تفاوت کپی‌پیست شده بود (نقض «no duplication» در Code Review
Checklist بخش ۱۵) — نه رفتار قبلی را می‌شکند، فقط آن را متمرکز می‌کند.

CircularProgress یک ring/donut سفارشی است چون Qt هیچ ویجت native برای
آن ندارد.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QProgressBar, QWidget
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from ui.style.theme_manager import colors, Radius


class BaseProgressBar(QProgressBar):
    """نوار پیشرفت نازک با رنگ accent قابل‌تنظیم.

    مثال:
        pb = BaseProgressBar(accent=colors().danger, height=6)
        pb.setValue(72)
    """

    def __init__(
        self,
        accent: Optional[str] = None,
        height: int = 6,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setRange(0, 100)
        self.setTextVisible(False)
        self.setFixedHeight(height)
        self._accent = accent
        self._apply_style()

    def set_accent(self, accent: str) -> None:
        self._accent = accent
        self._apply_style()

    def _apply_style(self) -> None:
        c = colors()
        accent = self._accent or c.primary
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c.border};
                border: none;
                border-radius: {self.height() // 2}px;
            }}
            QProgressBar::chunk {{
                background-color: {accent};
                border-radius: {self.height() // 2}px;
            }}
        """)


class CircularProgress(QWidget):
    """نوار پیشرفت دایره‌ای (ring) — برای نمایش درصد پیشرفت هدف/عادت
    به‌صورت فشرده‌تر از نوار خطی.

    مثال:
        ring = CircularProgress(value=68, accent=colors().success)
    """

    def __init__(
        self,
        value: int = 0,
        size: int = 64,
        thickness: int = 6,
        accent: Optional[str] = None,
        show_label: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._value = max(0, min(100, value))
        self._thickness = thickness
        self._accent = accent
        self._show_label = show_label
        self.setFixedSize(size, size)

    def set_value(self, value: int) -> None:
        self._value = max(0, min(100, value))
        self.update()

    def set_accent(self, accent: str) -> None:
        self._accent = accent
        self.update()

    def paintEvent(self, event) -> None:
        c = colors()
        accent = self._accent or c.primary
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = self._thickness / 2 + 1
        rect = QRectF(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)

        track_pen = QPen(QColor(c.border))
        track_pen.setWidth(self._thickness)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        value_pen = QPen(QColor(accent))
        value_pen.setWidth(self._thickness)
        value_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(value_pen)
        span_angle = int(360 * 16 * (self._value / 100))
        # شروع از ساعت ۱۲ (۹۰ درجه در مختصات Qt) و در جهت عقربه‌های ساعت
        painter.drawArc(rect, 90 * 16, -span_angle)

        if self._show_label:
            painter.setPen(QColor(c.text_primary))
            font = QFont()
            font.setPointSize(max(8, self.width() // 6))
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._value}%")

        painter.end()
