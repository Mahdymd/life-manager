"""ui/components/heatmap.py — نقشه‌ی حرارتی سبک GitHub (Phase 5).

طبق بخش ۴ اسپک (Habits view): "GitHub‑style heatmap".

شبکه‌ای از مربع‌های کوچک، هر ستون یک هفته و هر ردیف یک روز از هفته
(شنبه تا جمعه، مطابق تقویم فارسی) — رنگ هر مربع بر اساس شدت انجام
(مقدار count در جدول habit_logs) روشن‌تر/تیره‌تر می‌شود.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QSizePolicy, QToolTip
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QMouseEvent

from ui.style.theme_manager import colors
from utils.date_utils import format_jalali


class HabitHeatmap(QWidget):
    """نقشه‌ی حرارتی فشرده — پیش‌فرض ۱۲ هفته‌ی اخیر (مناسب کارت عادت).

    مثال:
        heatmap = HabitHeatmap(data={"2026-07-01": 1, "2026-07-03": 2},
                                accent=habit.color, weeks=12)
    """

    def __init__(
        self,
        data: Optional[Dict[str, int]] = None,
        accent: Optional[str] = None,
        weeks: int = 12,
        cell_size: int = 11,
        cell_gap: int = 3,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._data = data or {}
        self._accent = accent
        self._weeks = weeks
        self._cell_size = cell_size
        self._cell_gap = cell_gap
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._recalc_size()

    def _recalc_size(self) -> None:
        step = self._cell_size + self._cell_gap
        w = self._weeks * step + self._cell_gap
        h = 7 * step + self._cell_gap
        self.setFixedSize(w, h)

    def set_data(self, data: Dict[str, int], accent: Optional[str] = None) -> None:
        self._data = data
        if accent:
            self._accent = accent
        self.update()

    def _day_grid(self):
        """لیستی از (تاریخ, ستون, ردیف) برای شبکه‌ی ۱۲هفته‌ای منتهی به امروز."""
        today = date.today()
        # شنبه = ابتدای هفته (طبق تقویم فارسی): weekday() پایتون دوشنبه=۰
        # را می‌دهد؛ (weekday()+2)%7 تبدیل به شنبه=۰ می‌کند.
        days_since_saturday = (today.weekday() + 2) % 7
        end_of_week = today + timedelta(days=(6 - days_since_saturday))
        start = end_of_week - timedelta(days=self._weeks * 7 - 1)

        result = []
        for i in range(self._weeks * 7):
            d = start + timedelta(days=i)
            if d > today:
                continue
            col = i // 7
            row = i % 7
            result.append((d, col, row))
        return result

    def paintEvent(self, event) -> None:
        c = colors()
        accent = self._accent or c.success
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        step = self._cell_size + self._cell_gap

        for d, col, row in self._day_grid():
            count = self._data.get(d.isoformat(), 0)
            x = self._cell_gap + col * step
            y = self._cell_gap + row * step
            rect = QRectF(x, y, self._cell_size, self._cell_size)

            if count <= 0:
                color = QColor(c.border)
            else:
                # شدت رنگ بر اساس count (۱=روشن، ۳+=پررنگ‌ترین)
                alpha = min(255, 90 + count * 55)
                color = QColor(accent)
                color.setAlpha(alpha)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(rect, 2, 2)

        painter.end()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        step = self._cell_size + self._cell_gap
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        col = (pos.x() - self._cell_gap) // step
        row = (pos.y() - self._cell_gap) // step

        for d, c_, r_ in self._day_grid():
            if c_ == col and r_ == row:
                count = self._data.get(d.isoformat(), 0)
                label = format_jalali(g_date=d, fmt="named")
                text = f"{label} — {count} بار" if count else f"{label} — انجام نشده"
                global_pos = (event.globalPosition().toPoint()
                              if hasattr(event, "globalPosition") else event.globalPos())
                QToolTip.showText(global_pos, text, self)
                return
        QToolTip.hideText()
        super().mouseMoveEvent(event)
