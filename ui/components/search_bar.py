"""ui/components/search_bar.py — نوار جستجوی debounced (Phase 4).

طبق بخش ۹ اسپک: "CommandPalette, SearchBar" (CommandPalette از قبل در
command_palette.py وجود دارد).

این کامپوننت الگوی تکراری «QLineEdit + QTimer با تأخیر ۳۰۰ میلی‌ثانیه»
را که در tasks_page.py و notes_page.py جداگانه پیاده‌سازی شده بود،
یک‌جا جمع می‌کند.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QLineEdit, QWidget
from PySide6.QtCore import QTimer, Signal


class SearchBar(QLineEdit):
    """نوار جستجو با debounce — سیگنال search_requested فقط وقتی emit
    می‌شود که کاربر ۳۰۰ میلی‌ثانیه تایپ نکرده باشد (نه به ازای هر حرف).

    مثال:
        bar = SearchBar(placeholder="جستجو...")
        bar.search_requested.connect(self._vm.load)
    """

    search_requested = Signal(str)

    def __init__(
        self,
        placeholder: str = "جستجو...",
        debounce_ms: int = 300,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        from ui.style.theme_manager import colors
        from ui.style.icons import icon as _icon
        self.addAction(_icon("search", 15, colors().text_secondary),
                       QLineEdit.ActionPosition.LeadingPosition)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self._emit_search)
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, _text: str) -> None:
        self._timer.start()

    def _emit_search(self) -> None:
        self.search_requested.emit(self.text().strip())
