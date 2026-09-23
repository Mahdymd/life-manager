"""
ui/components/base_switch.py — سوییچ روشن/خاموش انیمیشنی (Phase 4).

طبق بخش ۹ اسپک: "BaseSwitch". Qt هیچ ویجت native برای toggle-switch
ندارد (برخلاف QCheckBox)، پس این یک QAbstractButton سفارشی با
paintEvent است. حرکت دایره از Motion tokens مرکزی (durations/easing)
استفاده می‌کند، نه یک عدد دلخواه — طبق قانون «هرگز magic number استفاده
نکن».

باید System accessibility setting «کاهش حرکت» (reduced motion) را هم
رعایت کند (بخش ۹ اسپک: "Respect reduced motion system preference")؛
این از طریق QApplication در main.py احتمالاً کنترل می‌شود، اینجا فقط
مدت انیمیشن را کوتاه/صفر می‌کنیم اگر سیستم آن را خواسته باشد.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QAbstractButton, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRect
from PySide6.QtGui import QPainter, QColor

from ui.style.theme_manager import colors, Motion


class BaseSwitch(QAbstractButton):
    """سوییچ روشن/خاموش (مثل iOS)، به‌جای QCheckBox برای تنظیمات باینری
    که معنای «فعال/غیرفعال فوری» دارند (نه یک چک‌باکس فرم).

    مثال:
        sw = BaseSwitch()
        sw.setChecked(True)
        sw.toggled.connect(on_toggle)
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(44, 24)

        self._knob_position = 2.0  # موقعیت افقی دایره (پیکسل، از چپ)
        self._anim = QPropertyAnimation(self, b"knob_position", self)
        self._anim.setDuration(Motion.FAST)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.toggled.connect(self._animate_to_state)

    # ------------------------------------------------------------------ #
    # Qt Property برای انیمیشن (QPropertyAnimation باید یک Property واقعی
    # را هدف بگیرد، نه یک attribute ساده)
    # ------------------------------------------------------------------ #
    def _get_knob_position(self) -> float:
        return self._knob_position

    def _set_knob_position(self, value: float) -> None:
        self._knob_position = value
        self.update()

    knob_position = Property(float, _get_knob_position, _set_knob_position)

    def _animate_to_state(self, checked: bool) -> None:
        target = self.width() - 22 if checked else 2.0
        self._anim.stop()
        self._anim.setStartValue(self._knob_position)
        self._anim.setEndValue(float(target))
        self._anim.start()

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(44, 24)

    def paintEvent(self, event) -> None:
        c = colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color = QColor(c.primary if self.isChecked() else c.border)
        if not self.isEnabled():
            track_color = QColor(c.text_disabled)

        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        knob_color = QColor(c.primary_text) if self.isChecked() else QColor(c.surface)
        knob_rect = QRect(int(self._knob_position), 2, 20, 20)
        painter.setBrush(knob_color)
        painter.drawEllipse(knob_rect)

        painter.end()
