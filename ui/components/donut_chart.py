"""ui/components/donut_chart.py — نمودار دونات (Phase 5).

طبق بخش ۵ اسپک (Expenses view): "donut chart" برای نمایش سهم هر
دسته‌بندی از کل هزینه‌ی ماه.

این یک کامپوننت عمومی است (نه مخصوص مالی) تا در آینده هر جای دیگری هم
قابل استفاده باشد — ورودی فقط لیستی از (label, value, color) است.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from ui.style.theme_manager import colors


Segment = Tuple[str, float, str]  # (label, value, color_hex)


class DonutChart(QWidget):
    """نمودار دونات با برچسب مرکزی اختیاری (مثلاً «کل هزینه»).

    مثال:
        chart = DonutChart([
            ("خوراک", 1_200_000, "#ef4444"),
            ("حمل‌ونقل", 400_000, "#f59e0b"),
            ("سرگرمی", 250_000, "#6366f1"),
        ], center_label="۱٫۸۵۰٬۰۰۰ تومان")
    """

    def __init__(
        self,
        segments: Optional[List[Segment]] = None,
        thickness: int = 22,
        size: int = 180,
        center_label: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._segments = segments or []
        self._thickness = thickness
        self._center_label = center_label
        self.setFixedSize(size, size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_data(self, segments: List[Segment], center_label: str = "") -> None:
        self._segments = segments
        self._center_label = center_label
        self.update()

    def paintEvent(self, event) -> None:
        c = colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = self._thickness / 2 + 2
        rect = QRectF(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)

        total = sum(v for _, v, _ in self._segments)

        if total <= 0:
            # حالت خالی: یک حلقه‌ی خاکستری کامل (به‌جای هیچ‌چیز — طبق
            # قانون «هرگز بدون empty state رها نکن»، حتی برای یک چارت)
            pen = QPen(QColor(c.border))
            pen.setWidth(self._thickness)
            painter.setPen(pen)
            painter.drawArc(rect, 0, 360 * 16)
        else:
            start_angle = 90 * 16  # شروع از ساعت ۱۲
            for label, value, color in self._segments:
                span = int(360 * 16 * (value / total))
                pen = QPen(QColor(color))
                pen.setWidth(self._thickness)
                pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                painter.setPen(pen)
                painter.drawArc(rect, start_angle, -span)
                start_angle -= span

        if self._center_label:
            painter.setPen(QColor(c.text_primary))
            font = QFont()
            font.setPointSize(max(9, self.width() // 14))
            font.setBold(True)
            painter.setFont(font)
            inner = rect.adjusted(self._thickness, self._thickness, -self._thickness, -self._thickness)
            painter.drawText(inner, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                             self._center_label)

        painter.end()
