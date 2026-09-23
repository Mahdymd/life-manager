"""
ui/components/card.py — Card, CardHeader, CardContent, CardFooter (Phase 4).

طبق بخش ۹ اسپک. QSS پایه (رنگ/border/radius) از قبل برای
`QFrame[class="card"]`/`[class="card-elevated"]` در ThemeManager تعریف
شده؛ این فایل ساختار داخلی (padding/spacing یکدست بر اساس Spacing
tokens) را اضافه می‌کند تا هر صفحه دیگر مجبور نباشد margins را دستی و
ناهماهنگ تنظیم کند (که در چند صفحه با مقادیر کمی متفاوت دیده شده بود).
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt

from ui.style.theme_manager import colors, Spacing, Elevation


class Card(QFrame):
    """کانتینر پایه‌ی کارت. می‌تواند CardHeader/CardContent/CardFooter
    را به‌ترتیب در خودش نگه دارد، یا مستقیم هر ویجت دیگری.

    مثال:
        card = Card(elevated=True)
        card.body.addWidget(CardHeader("عنوان"))
        card.body.addWidget(CardContent(some_widget))
        card.body.addWidget(CardFooter(ok_btn, cancel_btn))
    """

    def __init__(self, elevated: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card-elevated" if elevated else "card")
        self._elevated = elevated
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)
        if elevated:
            Elevation.apply(self, Elevation.SM)

    def addWidget(self, widget: QWidget) -> None:
        self.body.addWidget(widget)

    def enterEvent(self, event) -> None:
        """طبق بخش ۹ اسپک: "subtle scale on cards" — فقط برای کارت‌های
        elevated معنی دارد (کارت‌های flat اصلاً سایه‌ی پایه ندارند)."""
        if self._elevated:
            Elevation.apply(self, Elevation.MD)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self._elevated:
            Elevation.apply(self, Elevation.SM)
        super().leaveEvent(event)


class CardHeader(QWidget):
    """سربرگ کارت — عنوان + توضیح اختیاری، با padding یکدست."""

    def __init__(self, title: str, subtitle: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        c = colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet(f"font-size: 12px; color: {c.text_secondary}; background: transparent;")
            layout.addWidget(sub_lbl)


class CardContent(QWidget):
    """بدنه‌ی اصلی کارت با padding یکدست؛ هر ویجت دلخواه را در خودش می‌گذارد."""

    def __init__(self, content: Optional[QWidget] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.SM, Spacing.LG, Spacing.SM)
        layout.setSpacing(Spacing.SM)
        if content is not None:
            layout.addWidget(content)

    def addWidget(self, widget: QWidget) -> None:
        self.layout().addWidget(widget)


class CardFooter(QWidget):
    """پاورقی کارت — معمولاً دکمه‌های اقدام، چیده‌شده در راست (یا هر
    ترتیبی که پاس داده شود)، با یک جداکننده‌ی ظریف در بالا."""

    def __init__(self, *actions: QWidget, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        c = colors()
        self.setStyleSheet(f"border-top: 1px solid {c.border};")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.SM, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.SM)
        layout.addStretch()
        for action in actions:
            layout.addWidget(action)
