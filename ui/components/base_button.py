"""
ui/components/base_button.py — دکمه‌ی پایه‌ی برنامه (Phase 4).

طبق بخش ۹ اسپک: "BaseButton (variants: primary, secondary, outline,
ghost, danger; sizes: sm, md, lg)".

این کلاس یک لایه‌ی نازک و typed روی مکانیزم QSS موجود (پراپرتی داینامیک
`class`/`size` که در ThemeManager تعریف شده) است — معماری قبلی را
دور نمی‌زند، فقط یک API صریح و ایمن (enum به‌جای رشته‌ی جادویی) روی آن
می‌گذارد تا در کد جدید به‌جای `btn.setProperty("class","primary")`
بنویسیم `BaseButton("متن", variant=ButtonVariant.PRIMARY)`.

همه‌ی حالت‌های تعاملی (default/hover/pressed/disabled/focus) از قبل در
QSS مرکزی تعریف شده‌اند؛ این کلاس هیچ استایل inline اضافه نمی‌کند —
دقیقاً طبق قانون constitution («هرگز رنگ/spacing را hardcode نکن»).
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, QPointF
from PySide6.QtGui import QPainter, QColor, QPainterPath

from ui.style.theme_manager import colors, Motion


class ButtonVariant(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    OUTLINE = "outline"
    GHOST = "ghost"
    DANGER = "danger"


class ButtonSize(str, Enum):
    SM = "sm"
    MD = "md"
    LG = "lg"


class BaseButton(QPushButton):
    """دکمه‌ی استاندارد برنامه با variant و size صریح.

    مثال:
        btn = BaseButton("ذخیره", variant=ButtonVariant.PRIMARY, size=ButtonSize.LG)
        btn2 = BaseButton("حذف", variant=ButtonVariant.DANGER)
    """

    def __init__(
        self,
        text: str = "",
        variant: ButtonVariant = ButtonVariant.SECONDARY,
        size: ButtonSize = ButtonSize.MD,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        self._variant = variant
        self._size = size
        self.setProperty("class", variant.value)
        self.setProperty("size", size.value)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # focus policy صریح تا کیبورد-ناوبری (بخش ۱۲ اسپک) همیشه کار کند
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Ripple (بخش ۹ اسپک: "ripple on buttons")
        self._ripple_pos: Optional[QPointF] = None
        self._ripple_radius: float = 0.0
        self._ripple_opacity: float = 0.0
        self._ripple_anim = QVariantAnimation(self)
        self._ripple_anim.setDuration(Motion.SLOW)
        self._ripple_anim.setStartValue(0.0)
        self._ripple_anim.setEndValue(1.0)
        self._ripple_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._ripple_anim.valueChanged.connect(self._on_ripple_step)

    @property
    def variant(self) -> ButtonVariant:
        return self._variant

    def set_variant(self, variant: ButtonVariant) -> None:
        """variant دکمه را در زمان اجرا تغییر می‌دهد (مثلاً یک دکمه‌ی
        toggle که بین حالت عادی و danger جابه‌جا می‌شود)."""
        self._variant = variant
        self.setProperty("class", variant.value)
        self._repolish()

    @property
    def size_variant(self) -> ButtonSize:
        return self._size

    def set_size(self, size: ButtonSize) -> None:
        self._size = size
        self.setProperty("size", size.value)
        self._repolish()

    def _repolish(self) -> None:
        """بعد از تغییر پراپرتی داینامیک، Qt باید مجبور به بازخوانی QSS
        شود؛ در غیر این صورت تغییر تا rebuild بعدی ویجت نمایش داده
        نمی‌شود (یک نکته‌ی رایج و کم‌شناخته‌شده‌ی Qt Style Sheets)."""
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:
        if self.isEnabled():
            pos = event.position() if hasattr(event, "position") else event.pos()
            self._ripple_pos = QPointF(pos)
            self._ripple_anim.stop()
            self._ripple_anim.start()
        super().mousePressEvent(event)

    def _on_ripple_step(self, value: float) -> None:
        # شعاع تا گوشه‌ی دورترین دکمه رشد می‌کند، شفافیت هم‌زمان محو می‌شود
        max_radius = (self.width() ** 2 + self.height() ** 2) ** 0.5
        self._ripple_radius = value * max_radius
        self._ripple_opacity = 1.0 - value
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._ripple_pos is not None and self._ripple_opacity > 0.01:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            clip = QPainterPath()
            clip.addRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)
            painter.setClipPath(clip)
            color = QColor(colors().primary_text if self._variant == ButtonVariant.PRIMARY else colors().primary)
            color.setAlphaF(min(0.35, self._ripple_opacity * 0.35))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(self._ripple_pos, self._ripple_radius, self._ripple_radius)
            painter.end()
