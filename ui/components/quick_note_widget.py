"""ui/components/quick_note_widget.py — یادداشت سریع شناور (Phase 6).

طبق بخش ۶ اسپک: "Quick Note: system‑wide shortcut, floating
always‑on‑top note, auto‑saved to journal".

این ویجت یک پنجره‌ی کوچک، مستقل، همیشه-روی-بقیه (always-on-top) است که
با میان‌بر Ctrl+Shift+N باز/بسته می‌شود. برخلاف بقیه‌ی کامپوننت‌ها این
یک QWidget با WindowFlags مستقل است (نه فرزند صفحه‌ی جاری)، چون باید
حتی وقتی کاربر روی صفحه‌ی دیگری از برنامه است هم در دسترس باشد.

ذخیره‌سازی مستقیم و synchronous نیست — از الگوی BaseViewModel.run_async
مشابه بقیه‌ی برنامه استفاده می‌کند تا هرگز UI thread را قفل نکند، با
یک QuickNoteViewModel سبک اختصاصی.
"""

from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer, Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.style.theme_manager import colors, Spacing, Radius, Elevation
from core.services.journal_service import append_quick_note


class QuickNoteViewModel(BaseViewModel):
    """ViewModel مینیمال برای Quick Note — فقط یک عملیات دارد: ذخیره‌ی
    async متن در یادداشت روزانه‌ی امروز."""

    saved = Signal()

    def save(self, text: str) -> None:
        if not text or not text.strip():
            return
        self.run_async(append_quick_note, lambda _r: self.saved.emit(), text)


class QuickNoteWidget(QWidget):
    """پنجره‌ی شناور یادداشت سریع.

    مثال استفاده (در main_window.py):
        self._quick_note = QuickNoteWidget()
        QShortcut(QKeySequence("Ctrl+Shift+N"), self).activated.connect(
            self._quick_note.toggle)
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedSize(320, 220)

        self._vm = QuickNoteViewModel(self)
        self._vm.saved.connect(self._on_saved)

        c = colors()
        self.setStyleSheet(f"""
            QuickNoteWidget {{
                background-color: {c.surface_elev};
                border: 1px solid {c.primary};
                border-radius: {Radius.LG}px;
            }}
        """)
        Elevation.apply(self, Elevation.LG)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        header = QHBoxLayout()
        title = QLabel("یادداشت سریع")
        title.setStyleSheet("font-size: 13px; font-weight: 600; background: transparent;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setProperty("class", "icon")
        close_btn.setFixedSize(22, 22)
        close_btn.clicked.connect(self._save_and_close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self._editor = QTextEdit()
        self._editor.setPlaceholderText("همین‌جا بنویس... خودکار در یادداشت روزانه ذخیره می‌شود.")
        layout.addWidget(self._editor)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"font-size: 11px; color: {c.success}; background: transparent;")
        layout.addWidget(self._status_lbl)

        # ذخیره‌ی خودکار با debounce (نه به ازای هر حرف) — طبق همان
        # الگوی SearchBar (ui/components/search_bar.py)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(1500)
        self._save_timer.timeout.connect(self._auto_save)
        self._editor.textChanged.connect(lambda: self._save_timer.start())

    def toggle(self) -> None:
        if self.isVisible():
            self._save_and_close()
        else:
            self._editor.clear()
            self._status_lbl.setText("")
            self.show()
            self._center_on_screen()
            self._editor.setFocus()

    def _center_on_screen(self) -> None:
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + geo.width() - self.width() - 40
            y = geo.y() + geo.height() - self.height() - 60
            self.move(x, y)

    def _auto_save(self) -> None:
        text = self._editor.toPlainText().strip()
        if text:
            self._vm.save(text)

    def _on_saved(self) -> None:
        self._status_lbl.setText("ذخیره شد در یادداشت روزانه")

    def _save_and_close(self) -> None:
        text = self._editor.toPlainText().strip()
        if text:
            self._vm.save(text)
        self.hide()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._save_and_close()
        else:
            super().keyPressEvent(event)
