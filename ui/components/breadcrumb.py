"""ui/components/breadcrumb.py — Breadcrumb و SegmentedControl (Phase 4).

طبق بخش ۹ اسپک: "Breadcrumb" و "TabBar, SegmentedControl".

Breadcrumb: مسیر ناوبری («داشبورد > تسک‌ها > ویرایش»)، هر بخش قابل‌کلیک
(به‌جز آخری که مقصد فعلی است).

SegmentedControl: انتخاب تک‌گزینه‌ای بین چند گزینه‌ی هم‌عرض (جایگزین
سبک‌تر QComboBox برای ۲ تا ۴ گزینه — دقیقاً همان الگویی که در
finance_page.py برای انتخاب نوع تراکنش و focus_page.py برای انتخاب
حالت پومودورو دستی پیاده‌سازی شده بود، اینجا متمرکز شده).
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QButtonGroup
from PySide6.QtCore import Qt, Signal

from ui.style.theme_manager import colors, Spacing


class Breadcrumb(QWidget):
    """مسیر ناوبری قابل‌کلیک.

    Signals:
        segment_clicked(int): ایندکس بخشی که کلیک شده (۰-based).

    مثال:
        bc = Breadcrumb(["داشبورد", "تسک‌ها", "ویرایش"])
        bc.segment_clicked.connect(lambda i: print("رفتن به", i))
    """

    segment_clicked = Signal(int)

    def __init__(self, segments: List[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        c = colors()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.XS)

        for i, seg in enumerate(segments):
            is_last = i == len(segments) - 1
            if is_last:
                lbl = QLabel(seg)
                lbl.setStyleSheet(f"color: {c.text_primary}; font-weight: 600; font-size: 12px; background: transparent;")
                layout.addWidget(lbl)
            else:
                btn = QPushButton(seg)
                btn.setProperty("class", "ghost")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"color: {c.text_secondary}; font-size: 12px; padding: 2px 4px; min-height: 0;")
                btn.clicked.connect(lambda _checked, idx=i: self.segment_clicked.emit(idx))
                layout.addWidget(btn)

                sep = QLabel("›")
                sep.setStyleSheet(f"color: {c.text_disabled}; background: transparent;")
                layout.addWidget(sep)

        layout.addStretch()


class SegmentedControl(QWidget):
    """کنترل انتخاب تک‌گزینه‌ای بین چند گزینه (مثل iOS Segmented Control).

    Signals:
        value_changed(object): مقدار گزینه‌ی تازه‌انتخاب‌شده.

    مثال:
        seg = SegmentedControl([("income","درآمد"), ("expense","هزینه")])
        seg.value_changed.connect(on_type_changed)
    """

    value_changed = Signal(object)

    def __init__(self, options: List[Tuple], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        c = colors()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.XS)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}

        for value, label in options:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: 1px solid {c.border};
                    border-radius: 8px; padding: 6px 14px; font-size: 12px;
                }}
                QPushButton:checked {{
                    background: {c.primary}; color: {c.primary_text}; border-color: {c.primary};
                }}
                QPushButton:hover:!checked {{ background: {c.surface_elev}; }}
            """)
            btn.clicked.connect(lambda _checked, v=value: self.value_changed.emit(v))
            self._group.addButton(btn)
            self._buttons[value] = btn
            layout.addWidget(btn)

        layout.addStretch()
        if options:
            self._buttons[options[0][0]].setChecked(True)

    def set_value(self, value) -> None:
        btn = self._buttons.get(value)
        if btn:
            btn.setChecked(True)

    def value(self):
        for value, btn in self._buttons.items():
            if btn.isChecked():
                return value
        return None
