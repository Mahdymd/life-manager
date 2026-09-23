"""ui/pages/calendar_page.py — تقویم شمسی با رویدادها."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QGridLayout, QDialog, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QListWidget, QListWidgetItem,
    QScrollArea, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from utils.date_utils import (
    gregorian_to_jalali, jalali_to_gregorian, today_jalali,
    format_jalali, parse_jalali_input, iran_weekday, days_in_jalali_month,
)
from ui.pages.base_page import BasePage
from ui.style.theme_manager import colors
from ui.viewmodels.calendar_viewmodel import CalendarViewModel
from ui.components.confirm_dialog import confirm
import config
from datetime import date


class EventFormDialog(QDialog):
    def __init__(self, parent=None, event=None, default_date=None):
        super().__init__(parent)
        self.setWindowTitle("رویداد جدید" if not event else "ویرایش رویداد")
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setMinimumWidth(420)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        hdr = QLabel("" + self.windowTitle())
        hdr.setStyleSheet("font-size:17px;font-weight:700;background:transparent;")
        layout.addWidget(hdr)

        form = QFormLayout()
        form.setSpacing(10)
        self._title = QLineEdit()
        form.addRow("عنوان *:", self._title)
        self._date = QLineEdit()
        if default_date:
            self._date.setText(format_jalali(default_date))
        form.addRow("تاریخ *:", self._date)
        self._time = QLineEdit()
        self._time.setPlaceholderText("مثال: 14:30 (اختیاری)")
        form.addRow("ساعت:", self._time)
        self._type = QComboBox()
        self._type.addItem("شخصی", "personal")
        self._type.addItem("تولد", "birthday")
        self._type.addItem("سالگرد", "anniversary")
        self._type.addItem("یادآوری", "reminder")
        form.addRow("نوع:", self._type)
        self._desc = QTextEdit()
        self._desc.setMaximumHeight(70)
        form.addRow("توضیحات:", self._desc)
        layout.addLayout(form)

        if event:
            self._title.setText(event.title)
            self._date.setText(format_jalali(iso_str=event.date))
            self._time.setText(event.time or "")
            idx = self._type.findData(event.type.value)
            if idx >= 0: self._type.setCurrentIndex(idx)
            self._desc.setPlainText(event.description or "")

        btns = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.clicked.connect(self.reject)
        save = QPushButton("ذخیره")
        save.setProperty("class", "primary")
        save.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _save(self):
        if not self._title.text().strip() or not self._date.text().strip():
            return
        self.accept()

    def get_data(self):
        d = parse_jalali_input(self._date.text())
        return {
            "title": self._title.text().strip(),
            "date": d.isoformat() if d else date.today().isoformat(),
            "time": self._time.text().strip() or None,
            "type": self._type.currentData(),
            "description": self._desc.toPlainText().strip() or None,
            "is_all_day": not bool(self._time.text().strip()),
        }


class CalendarPage(BasePage):
    """View خالص — بدون import مستقیم از core.repositories؛ همه چیز از
    طریق self._vm (CalendarViewModel)."""

    def setup_ui(self):
        self._vm = CalendarViewModel(self)
        self._vm.events_changed.connect(self._on_events_changed)
        self._vm.error_occurred.connect(self._show_error)

        self.set_header("تقویم", "")
        add_btn = self.add_header_action("+ رویداد جدید")
        add_btn.clicked.connect(lambda: self._open_form())

        nav_row = QHBoxLayout()
        prev_btn = QPushButton("‹")
        prev_btn.setProperty("class", "icon")
        prev_btn.clicked.connect(self._prev_month)
        next_btn = QPushButton("›")
        next_btn.setProperty("class", "icon")
        next_btn.clicked.connect(self._next_month)
        self._month_lbl = QLabel("")
        self._month_lbl.setStyleSheet("font-size:18px;font-weight:700;background:transparent;")
        today_btn = QPushButton("امروز")
        today_btn.clicked.connect(self._goto_today)
        nav_row.addWidget(prev_btn)
        nav_row.addWidget(self._month_lbl)
        nav_row.addWidget(next_btn)
        nav_row.addStretch()
        nav_row.addWidget(today_btn)
        self._content_layout.addLayout(nav_row)

        # Calendar grid
        self._grid_frame = QFrame()
        self._grid = QGridLayout(self._grid_frame)
        self._grid.setSpacing(4)
        self._content_layout.addWidget(self._grid_frame)

        jy, jm, jd = today_jalali()
        self._cur_year = jy
        self._cur_month = jm
        self._selected_date = date.today().isoformat()
        self.refresh()

    def _prev_month(self):
        self._cur_month -= 1
        if self._cur_month < 1:
            self._cur_month = 12
            self._cur_year -= 1
        self.refresh()

    def _next_month(self):
        self._cur_month += 1
        if self._cur_month > 12:
            self._cur_month = 1
            self._cur_year += 1
        self.refresh()

    def _goto_today(self):
        jy, jm, jd = today_jalali()
        self._cur_year, self._cur_month = jy, jm
        self.refresh()

    def refresh(self):
        self._vm.load(self._cur_year, self._cur_month)

    def _on_events_changed(self, events: list):
        self._month_lbl.setText(
            f"{config.MONTHS_FA[self._cur_month-1]} {self._cur_year}")

        # Clear grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Header row (weekdays)
        tc = colors()
        for i, wd in enumerate(config.WEEKDAY_FA):
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-size:11px;color:{tc.text_secondary};font-weight:600;background:transparent;padding:4px;")
            self._grid.addWidget(lbl, 0, i)

        events_by_date = {}
        for e in events:
            events_by_date.setdefault(e.date, []).append(e)

        days_in_month = days_in_jalali_month(self._cur_year, self._cur_month)
        try:
            first_g = jalali_to_gregorian(self._cur_year, self._cur_month, 1)
            start_col = iran_weekday(first_g)
        except Exception:
            start_col = 0

        today_iso_str = date.today().isoformat()
        row = 1
        col = start_col
        for day in range(1, days_in_month + 1):
            try:
                g_date = jalali_to_gregorian(self._cur_year, self._cur_month, day)
            except Exception:
                continue
            iso = g_date.isoformat()
            is_today = iso == today_iso_str
            day_events = events_by_date.get(iso, [])

            cell = QFrame()
            cell.setProperty("class", "card")
            cell.setMinimumHeight(70)
            cell.setCursor(Qt.CursorShape.PointingHandCursor)
            if is_today:
                cell.setStyleSheet(f"QFrame{{background:{tc.primary}22;border:1px solid {tc.primary};border-radius:8px;}}")
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(6, 4, 6, 4)
            cl.setSpacing(2)
            day_lbl = QLabel(str(day))
            day_lbl.setStyleSheet(
                f"font-size:13px;font-weight:{'700' if is_today else '500'};"
                f"color:{tc.primary if is_today else tc.text_primary};background:transparent;")
            cl.addWidget(day_lbl)
            for ev in day_events[:2]:
                ev_lbl = QLabel(ev.title[:12])
                ev_lbl.setStyleSheet(
                    f"font-size:9px;background:{ev.color}33;color:{ev.color};"
                    f"border-radius:4px;padding:1px 4px;")
                cl.addWidget(ev_lbl)
            if len(day_events) > 2:
                more_lbl = QLabel(f"+{len(day_events)-2}")
                more_lbl.setStyleSheet(f"font-size:9px;color:{tc.text_secondary};background:transparent;")
                cl.addWidget(more_lbl)
            cl.addStretch()
            cell.mousePressEvent = lambda e, d=iso: self._on_day_click(d)
            self._grid.addWidget(cell, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _on_day_click(self, iso_date: str):
        self._selected_date = iso_date
        self._open_form(default_date=date.fromisoformat(iso_date))

    def _open_form(self, event=None, default_date=None):
        dlg = EventFormDialog(self, event, default_date or date.today())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if event:
                self._vm.update_event(event.id, **data)
            else:
                self._vm.add_event(**data)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
