"""
ui/components/badge.py — Badge و Chip (Phase 4).

Badge: نشانگر کوچک وضعیت/شمارش (مثلاً «فوری»، «۳ مورد جدید») — فقط
خواندنی، غیرقابل‌کلیک.
Chip: مثل Badge اما قابل‌حذف (با دکمه‌ی ×) و/یا قابل‌کلیک — برای
فیلترهای فعال، تگ‌ها.

هر دو رنگشان را از یک `accent` می‌گیرند که پیش‌فرضش colors().primary
است، نه یک hex ثابت.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, Signal

from ui.style.theme_manager import colors, Spacing, Radius


class Badge(QLabel):
    """نشانگر وضعیت غیرقابل‌کلیک.

    مثال:
        Badge("فوری", accent=colors().danger)
    """

    def __init__(self, text: str, accent: Optional[str] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        c = colors()
        self._accent = accent or c.primary
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            background-color: {self._accent}22;
            color: {self._accent};
            border-radius: {Radius.MD}px;
            padding: 2px {Spacing.SM}px;
            font-size: 11px;
            font-weight: 600;
        """)

    def set_accent(self, accent: str) -> None:
        self._accent = accent
        self._apply_style()


class Chip(QWidget):
    """تگ قابل‌حذف/قابل‌کلیک (برای فیلترهای فعال یا لیست دسته‌بندی‌ها).

    Signals:
        removed(): وقتی دکمه‌ی × کلیک شود (فقط اگر removable=True).
        clicked(): وقتی روی خودِ چیپ کلیک شود.
    """

    removed = Signal()
    clicked = Signal()

    def __init__(
        self,
        text: str,
        accent: Optional[str] = None,
        removable: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        c = colors()
        self._accent = accent or c.primary
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.SM + 2, 2, Spacing.SM + 2, 2)
        layout.setSpacing(Spacing.XS)

        self._label = QLabel(text)
        self._label.setStyleSheet(f"color: {self._accent}; font-size: 12px; font-weight: 500; background: transparent;")
        layout.addWidget(self._label)

        if removable:
            close_btn = QPushButton("×")
            close_btn.setFixedSize(16, 16)
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none; color: {self._accent};
                    font-size: 11px; padding: 0;
                }}
                QPushButton:hover {{ color: {c.danger}; }}
            """)
            close_btn.clicked.connect(self.removed.emit)
            layout.addWidget(close_btn)

        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            Chip {{
                background-color: {self._accent}18;
                border: 1px solid {self._accent}44;
                border-radius: {Radius.XL}px;
            }}
        """)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)
