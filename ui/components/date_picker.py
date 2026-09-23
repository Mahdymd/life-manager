"""ui/components/date_picker.py — انتخاب‌گر تاریخ شمسی (Phase 4).

طبق بخش ۹ اسپک: "DatePicker, Calendar".

نکته‌ی حیاتی: Qt یک `QCalendarWidget` بومی دارد، اما فقط میلادی است.
چون کل برنامه (fromat_jalali، parse_jalali_input، تقویم صفحه‌ی
calendar_page.py) بر پایه‌ی تاریخ شمسی است، از QCalendarWidget استفاده
نمی‌کنیم — این یک پیاده‌سازی سفارشی است که مستقیم از همان توابع تبدیل
utils/date_utils.py استفاده می‌کند (نه منطق تبدیل جدید و موازی).

قبلاً هر دیالوگی که تاریخ می‌گرفت (TaskFormDialog, EventFormDialog, ...)
یک QLineEdit ساده با پارس دستی متن («۱۴۰۴/۰۳/۱۵») داشت — این کامپوننت
یک جایگزین گرافیکی و خطاناپذیرتر است، بدون اینکه ورودی متنی قدیمی را
از بین ببرد (صفحات می‌توانند تدریجی مهاجرت کنند).
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QPoint

from ui.style.theme_manager import colors, Spacing, Radius, Elevation
from utils.date_utils import gregorian_to_jalali, jalali_to_gregorian, today_jalali
import config


class JalaliCalendarPopup(QFrame):
    """پاپ‌آپ شبکه‌ی روزهای یک ماه شمسی (frameless overlay).

    Signals:
        date_selected(str): تاریخ ISO (میلادی، برای ذخیره در دیتابیس)
            انتخاب‌شده توسط کاربر.
    """

    date_selected = Signal(str)

    def __init__(self, initial: Optional[date] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        c = colors()
        self.setStyleSheet(f"""
            JalaliCalendarPopup {{
                background-color: {c.surface_elev};
                border: 1px solid {c.border};
                border-radius: {Radius.LG}px;
            }}
        """)
        Elevation.apply(self, Elevation.MD)

        base = initial or date.today()
        self._jy, self._jm, _ = gregorian_to_jalali(base)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        outer.setSpacing(Spacing.SM)

        nav = QHBoxLayout()
        self._prev_btn = QPushButton("‹")
        self._prev_btn.setProperty("class", "icon")
        self._prev_btn.clicked.connect(self._prev_month)
        self._month_lbl = QLabel()
        self._month_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._month_lbl.setStyleSheet("font-weight: 600; font-size: 13px; background: transparent;")
        self._next_btn = QPushButton("›")
        self._next_btn.setProperty("class", "icon")
        self._next_btn.clicked.connect(self._next_month)
        nav.addWidget(self._prev_btn)
        nav.addWidget(self._month_lbl, 1)
        nav.addWidget(self._next_btn)
        outer.addLayout(nav)

        self._grid = QGridLayout()
        self._grid.setSpacing(2)
        outer.addLayout(self._grid)

        today_btn = QPushButton("امروز")
        today_btn.setProperty("class", "ghost")
        today_btn.clicked.connect(self._go_today)
        outer.addWidget(today_btn)

        self._render_month()

    def _prev_month(self) -> None:
        self._jm -= 1
        if self._jm < 1:
            self._jm = 12
            self._jy -= 1
        self._render_month()

    def _next_month(self) -> None:
        self._jm += 1
        if self._jm > 12:
            self._jm = 1
            self._jy += 1
        self._render_month()

    def _go_today(self) -> None:
        jy, jm, jd = today_jalali()
        self._jy, self._jm = jy, jm
        self._render_month()
        self._emit_day(jd)

    def _days_in_jalali_month(self, jy: int, jm: int) -> int:
        if jm <= 6:
            return 31
        if jm <= 11:
            return 30
        # اسفند: ۲۹ یا ۳۰ (سال کبیسه) — با تبدیل روز ۳۰ به میلادی و
        # برگشت، به‌جای فرمول کبیسه‌ی جداگانه (طبق قانون «منطق تبدیل را
        # تکرار نکن»، همان مسیر jalali_to_gregorian/gregorian_to_jalali
        # موجود را منبع حقیقت قرار می‌دهیم)
        try:
            jalali_to_gregorian(jy, 12, 30)
            return 30
        except Exception:
            return 29

    def _render_month(self) -> None:
        c = colors()
        self._month_lbl.setText(f"{config.MONTHS_FA[self._jm-1]} {self._jy}")

        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, wd in enumerate(config.WEEKDAY_FA):
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-size: 10px; color: {c.text_secondary}; background: transparent;")
            self._grid.addWidget(lbl, 0, i)

        first_of_month_g = jalali_to_gregorian(self._jy, self._jm, 1)
        start_weekday = (first_of_month_g.weekday() + 1) % 7  # شنبه=۰

        days = self._days_in_jalali_month(self._jy, self._jm)
        today_jy, today_jm, today_jd = today_jalali()

        row, col = 1, start_weekday
        for day in range(1, days + 1):
            btn = QPushButton(str(day))
            btn.setFixedSize(30, 26)
            is_today = (self._jy, self._jm, day) == (today_jy, today_jm, today_jd)
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: none; border-radius: {Radius.SM}px;
                    background: {c.primary + '22' if is_today else 'transparent'};
                    color: {c.primary if is_today else c.text_primary};
                    font-weight: {'700' if is_today else '400'};
                }}
                QPushButton:hover {{ background: {c.surface}; }}
            """)
            btn.clicked.connect(lambda _checked, d=day: self._emit_day(d))
            self._grid.addWidget(btn, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _emit_day(self, jd: int) -> None:
        g_date = jalali_to_gregorian(self._jy, self._jm, jd)
        self.date_selected.emit(g_date.isoformat())
        self.close()


class JalaliDateEdit(QWidget):
    """دکمه‌ای که تاریخ فعلی را نشان می‌دهد و با کلیک، پاپ‌آپ تقویم
    شمسی را باز می‌کند.

    Signals:
        date_changed(str): تاریخ ISO میلادی تازه‌انتخاب‌شده.

    مثال:
        picker = JalaliDateEdit()
        picker.date_changed.connect(lambda iso: print(iso))
        picker.set_date_iso(task.due_date)
    """

    date_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._value: Optional[date] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._btn = QPushButton("انتخاب تاریخ")
        self._btn.setProperty("class", "secondary")
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(self._open_popup)
        layout.addWidget(self._btn)

    def _open_popup(self) -> None:
        popup = JalaliCalendarPopup(self._value, self)
        popup.date_selected.connect(self._on_selected)
        pos = self.mapToGlobal(QPoint(0, self.height()))
        popup.move(pos)
        popup.show()

    def _on_selected(self, iso_date: str) -> None:
        self._value = date.fromisoformat(iso_date)
        self._refresh_label()
        self.date_changed.emit(iso_date)

    def _refresh_label(self) -> None:
        if not self._value:
            self._btn.setText("انتخاب تاریخ")
            return
        jy, jm, jd = gregorian_to_jalali(self._value)
        self._btn.setText(f"{jd} {config.MONTHS_FA[jm-1]} {jy}")

    def set_date_iso(self, iso_date: Optional[str]) -> None:
        self._value = date.fromisoformat(iso_date) if iso_date else None
        self._refresh_label()

    def date_iso(self) -> Optional[str]:
        return self._value.isoformat() if self._value else None
