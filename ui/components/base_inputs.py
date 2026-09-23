"""
ui/components/base_inputs.py — ویجت‌های پایه‌ی ورودی (Phase 4).

طبق بخش ۹ اسپک: "BaseLineEdit, BaseTextEdit, BaseComboBox, BaseCheckBox".

استایل پایه (default/hover/focus/disabled) از قبل در QSS مرکزی
(ThemeManager) برای QLineEdit/QTextEdit/QComboBox/QCheckBox تعریف شده؛
این کلاس‌ها یک لایه‌ی نازک روی آن‌ها می‌گذارند تا حالت «error» را که در
QSS پایه وجود نداشت اضافه کنند (طبق Definition of Done بخش ۱۶:
"All interactive states: ... error"). خودِ رنگ خطا از طریق selector
`[error="true"]` در QSS مرکزی می‌آید، نه استایل موردی این‌جا — تا با
تغییر تم (روشن/تاریک) به‌درستی sync بماند.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QLineEdit, QTextEdit, QComboBox, QCheckBox, QWidget


class _ErrorStateMixin:
    """Mixin مشترک برای افزودن حالت error به یک ویجت ورودی.

    باید در MRO قبل از کلاس Qt قرار بگیرد (مثل
    `class BaseLineEdit(_ErrorStateMixin, QLineEdit)`).
    """

    def _init_error_state(self) -> None:
        self._has_error = False

    def set_error(self, has_error: bool) -> None:
        """حالت خطا را روشن/خاموش می‌کند (حاشیه‌ی قرمز از QSS مرکزی می‌آید)."""
        self._has_error = has_error
        self.setProperty("error", "true" if has_error else "")
        self.style().unpolish(self)
        self.style().polish(self)

    @property
    def has_error(self) -> bool:
        return getattr(self, "_has_error", False)


class BaseLineEdit(_ErrorStateMixin, QLineEdit):
    """QLineEdit با پشتیبانی از حالت error.

    مثال:
        edit = BaseLineEdit()
        if not edit.text().strip():
            edit.set_error(True)
    """

    def __init__(self, placeholder: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_error_state()
        if placeholder:
            self.setPlaceholderText(placeholder)


class BaseTextEdit(_ErrorStateMixin, QTextEdit):
    """QTextEdit با پشتیبانی از حالت error."""

    def __init__(self, placeholder: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_error_state()
        if placeholder:
            self.setPlaceholderText(placeholder)


class BaseComboBox(_ErrorStateMixin, QComboBox):
    """QComboBox با پشتیبانی از حالت error و یک متد راحت برای پر کردن
    از لیست (value, label)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_error_state()

    def populate(self, items: list) -> None:
        """items: لیستی از (value, label) — جایگزین حلقه‌ی دستی
        addItem در همه‌ی صفحات."""
        self.clear()
        for value, label in items:
            self.addItem(label, value)

    def set_current_value(self, value) -> None:
        idx = self.findData(value)
        if idx >= 0:
            self.setCurrentIndex(idx)


class BaseCheckBox(QCheckBox):
    """QCheckBox با ظاهر یکدست (QSS مرکزی از قبل کامل پوشش می‌دهد؛ این
    کلاس صرفاً برای یکدستی نام‌گذاری با بقیه‌ی BaseXxx ها است)."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
