"""ui/components/confetti.py — انیمیشن جشن کانفتی (Phase 9).

طبق بخش ۹ اسپک: "completion celebration (confetti for streaks)".

پیاده‌سازی سبک: یک overlay شفاف موقت روی صفحه‌ی فعلی که چند ده تکه‌ی
رنگی را با فیزیک ساده (سقوط + چرخش) پایین می‌ریزد و بعد از ۲-۳ ثانیه
خودش را حذف می‌کند. از QPropertyAnimation سنگین برای هر ذره استفاده
نمی‌شود (برای ۵۰+ ذره عملکرد ضعیف می‌شد)؛ به‌جایش یک QTimer با گام‌های
دستی فیزیک، سبک‌تر و برای این تعداد ذره مناسب‌تر است.
"""

from __future__ import annotations
import random
from typing import List, Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor

from ui.style.theme_manager import colors


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "angle", "spin", "color", "size")

    def __init__(self, x: float, y: float, color: QColor):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3.0, 3.0)
        self.vy = random.uniform(-8.0, -3.0)
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-12, 12)
        self.color = color
        self.size = random.uniform(6, 11)

    def step(self, gravity: float) -> None:
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        self.angle += self.spin


class ConfettiOverlay(QWidget):
    """Overlay موقت کانفتی — روی parent (معمولاً صفحه‌ی جاری) نمایش
    داده می‌شود و بعد از پایان انیمیشن خودش را deleteLater می‌کند.

    مثال:
        ConfettiOverlay.celebrate(self)  # self: هر QWidget زنده (مثلاً یک صفحه)
    """

    _ACCENT_COLORS = ["primary", "success", "warning", "danger", "info", "accent_purple"]

    def __init__(self, parent: QWidget, particle_count: int = 60) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        if parent:
            self.setGeometry(parent.rect())

        c = colors()
        palette = [QColor(getattr(c, name, c.primary)) for name in self._ACCENT_COLORS]
        width = self.width() or 400
        self._particles: List[_Particle] = [
            _Particle(
                x=random.uniform(0, width),
                y=random.uniform(-40, 0),
                color=random.choice(palette),
            )
            for _ in range(particle_count)
        ]

        self._elapsed_ms = 0
        self._duration_ms = 2200
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps

        self.show()
        self.raise_()

    def _tick(self) -> None:
        self._elapsed_ms += 16
        for p in self._particles:
            p.step(gravity=0.28)
        self.update()
        if self._elapsed_ms >= self._duration_ms:
            self._timer.stop()
            self.deleteLater()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for p in self._particles:
            painter.save()
            painter.translate(p.x, p.y)
            painter.rotate(p.angle)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(p.color)
            painter.drawRoundedRect(QRectF(-p.size / 2, -p.size / 4, p.size, p.size / 2), 2, 2)
            painter.restore()
        painter.end()

    @staticmethod
    def celebrate(parent: QWidget, particle_count: int = 60) -> "ConfettiOverlay":
        """میان‌بر استاندارد — یک‌خطی برای فراخوانی از هر صفحه.

        مثال:
            from ui.components.confetti import ConfettiOverlay
            ConfettiOverlay.celebrate(self)
        """
        return ConfettiOverlay(parent, particle_count)
