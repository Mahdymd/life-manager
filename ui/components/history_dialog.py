"""ui/components/history_dialog.py — دیالوگ تاریخچه/بازگردانی نسخه (Phase 6).

طبق بخش ۶ اسپک (Smart Features): "Version History: restore previous
versions of tasks/journal entries". این قابلیت از فاز ۲ کامل در
core/services/history_service.py وجود داشت (entity_history table،
get_history، restore_snapshot) اما هیچ UI ای برایش ساخته نشده بود.

این یک کامپوننت عمومی است — هر صفحه‌ای که به Version History نیاز دارد
(فعلاً: tasks_page.py، در آینده: journal_page.py) همین را می‌تواند
با یک ViewModel-callback مناسب صدا بزند.
"""

from __future__ import annotations
from typing import Callable, List, Optional
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
from PySide6.QtCore import Qt, Signal

from ui.components.base_dialog import BaseDialog
from ui.style.theme_manager import colors
from utils.date_utils import format_jalali


class HistoryDialog(BaseDialog):
    """نمایش نسخه‌های قبلی یک رکورد (task یا journal_entry) با امکان
    بازگردانی به هرکدام.

    Signals:
        restore_requested(int): history_id ای که کاربر خواسته بازگردانی شود.

    مثال:
        dlg = HistoryDialog(self, "تاریخچه‌ی تسک", entries)
        dlg.restore_requested.connect(self._vm.restore_from_history)
        dlg.exec()
    """

    restore_requested = Signal(int)

    def __init__(self, parent, title: str, entries: List, parent_titles: dict = None):
        super().__init__(title, parent, min_width=440)
        self._entries = entries
        self._title_key = "title"  # کلیدی که برای پیش‌نمایش snapshot استفاده می‌شود

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setMinimumHeight(320)
        inner = QWidget()
        self._rows_layout = QVBoxLayout(inner)
        self._rows_layout.setSpacing(8)
        self._rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(inner)
        self.body.addWidget(scroll)

        self._render_rows()

        close_btn = QPushButton("بستن")
        close_btn.setProperty("class", "secondary")
        close_btn.clicked.connect(self.accept)
        self.body.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignLeft)

    def _render_rows(self):
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        c = colors()
        if not self._entries:
            lbl = QLabel("هنوز هیچ تغییری برای این مورد ثبت نشده.")
            lbl.setStyleSheet(f"color:{c.text_secondary};background:transparent;font-size:12px;")
            self._rows_layout.addWidget(lbl)
            return

        for entry in self._entries:
            row_frame = QWidget()
            row = QVBoxLayout(row_frame)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)

            from ui.style.icons import icon as _icon
            top = QHBoxLayout()
            is_delete = entry.change_type == "delete"
            change_color = c.danger if is_delete else c.warning
            badge_icon = QLabel()
            badge_icon.setPixmap(_icon("trash" if is_delete else "edit", 11, change_color).pixmap(11, 11))
            top.addWidget(badge_icon)
            badge = QLabel("حذف‌شده" if is_delete else "ویرایش‌شده")
            badge.setStyleSheet(f"color:{change_color};font-size:11px;font-weight:600;background:transparent;")
            top.addWidget(badge)
            top.addStretch()
            time_lbl = QLabel(format_jalali(iso_str=entry.changed_at, fmt="named"))
            time_lbl.setStyleSheet(f"color:{c.text_secondary};font-size:11px;background:transparent;")
            top.addWidget(time_lbl)
            row.addLayout(top)

            preview_text = entry.snapshot.get(self._title_key) or entry.snapshot.get("content") or ""
            if preview_text:
                preview_lbl = QLabel(str(preview_text)[:80])
                preview_lbl.setStyleSheet("font-size:13px;background:transparent;")
                preview_lbl.setWordWrap(True)
                row.addWidget(preview_lbl)

            restore_btn = QPushButton("بازگردانی به این نسخه")
            restore_btn.setProperty("class", "outline")
            restore_btn.clicked.connect(lambda _c=False, hid=entry.id: self.restore_requested.emit(hid))
            row.addWidget(restore_btn, 0, Qt.AlignmentFlag.AlignLeft)

            row_frame.setProperty("class", "card")
            row_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self._rows_layout.addWidget(row_frame)
