"""ui/components/focus_overlay.py — نمای تمام‌صفحه‌ی حالت فوکوس (Phase 6).

طبق بخش ۶ اسپک: "Focus Mode: Pomodoro / Deep Work timer, full‑screen
overlay, session logging". ثبت جلسه (session logging) از قبل در
focus_page.py/FocusViewModel وجود دارد؛ این کامپوننت فقط نمای
تمام‌صفحه‌ی بدون‌حواس‌پرتی را اضافه می‌کند.

نکته‌ی معماری مهم: این ویجت خودش یک تایمر مستقل نمی‌سازد (که باعث دو
منبع حقیقت متناقض می‌شد)، فقط نمایشگر تایمر موجود در FocusPage است —
FocusPage با هر tick متن این ویجت را هم (اگر باز باشد) به‌روزرسانی
می‌کند.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.style.theme_manager import colors


class FocusOverlay(QWidget):
    """نمای تمام‌صفحه‌ی بدون‌حواس‌پرتی برای حالت فوکوس.

    Signals:
        toggle_requested(): کاربر دکمه‌ی مکث/ادامه را زده.
        exit_requested(): کاربر خواسته از حالت تمام‌صفحه خارج شود
            (دکمه‌ی خروج یا Escape).

    مثال:
        overlay = FocusOverlay()
        overlay.toggle_requested.connect(self._toggle_timer)
        overlay.exit_requested.connect(overlay.close)
        overlay.set_time_text("24:59")
        overlay.showFullScreen()
    """

    toggle_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window)
        c = colors()
        self.setStyleSheet(f"background-color: {c.bg};")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)

        self._mode_lbl = QLabel("حالت فوکوس")
        self._mode_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mode_lbl.setStyleSheet(f"font-size:18px;color:{c.text_secondary};background:transparent;")
        layout.addWidget(self._mode_lbl)

        self._time_lbl = QLabel("25:00")
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 96, QFont.Weight.Bold)
        self._time_lbl.setFont(font)
        self._time_lbl.setStyleSheet(f"color:{c.primary};background:transparent;")
        layout.addWidget(self._time_lbl)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.setSpacing(16)

        self._toggle_btn = QPushButton("مکث")
        self._toggle_btn.setProperty("class", "primary")
        self._toggle_btn.setFixedWidth(140)
        self._toggle_btn.clicked.connect(self.toggle_requested.emit)
        btn_row.addWidget(self._toggle_btn)

        exit_btn = QPushButton("خروج از تمام‌صفحه")
        exit_btn.setProperty("class", "secondary")
        exit_btn.setFixedWidth(160)
        exit_btn.clicked.connect(self.exit_requested.emit)
        btn_row.addWidget(exit_btn)

        layout.addLayout(btn_row)

        hint = QLabel("Esc برای خروج")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"font-size:12px;color:{c.text_disabled};background:transparent;")
        layout.addWidget(hint)

    def set_time_text(self, text: str) -> None:
        self._time_lbl.setText(text)

    def set_mode_text(self, text: str) -> None:
        self._mode_lbl.setText(text)

    def set_running(self, is_running: bool) -> None:
        self._toggle_btn.setText("مکث" if is_running else "ادامه")

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.exit_requested.emit()
        else:
            super().keyPressEvent(event)
