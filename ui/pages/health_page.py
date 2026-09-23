"""ui/pages/health_page.py — صفحه سلامت."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QComboBox, QDialog, QFormLayout,
    QDoubleSpinBox, QSpinBox, QListWidget, QListWidgetItem,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from ui.pages.base_page import BasePage
from ui.components.stat_card import StatCard
from ui.style.theme_manager import colors
from ui.viewmodels.health_viewmodel import HealthViewModel
from utils.date_utils import today_iso, format_jalali


class QuickLogDialog(QDialog):
    """دیالوگ ثبت سریع متریک سلامت."""
    def __init__(self, parent=None, metric_type="weight"):
        super().__init__(parent)
        self._type = metric_type
        labels = {
            "weight": ("scale",   "ثبت وزن", "وزن (کیلوگرم)", 0, 300, 1, 70),
            "water":  ("droplet", "ثبت آب",  "تعداد لیوان",   0, 30,  0, 4),
            "sleep":  ("moon",    "ثبت خواب", "ساعت خواب",     0, 24,  1, 7),
        }
        icon_name, title, label, lo, hi, dec, default = labels.get(metric_type, labels["weight"])
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setMinimumWidth(340)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        from ui.style.icons import icon as _icon
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(8)
        hdr_icon_lbl = QLabel()
        hdr_icon_lbl.setPixmap(_icon(icon_name, 17, colors().text_primary).pixmap(17, 17))
        hdr_row.addWidget(hdr_icon_lbl)
        hdr = QLabel(title)
        hdr.setStyleSheet("font-size:16px;font-weight:700;background:transparent;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        form = QFormLayout()
        self._value = QDoubleSpinBox()
        self._value.setRange(lo, hi)
        self._value.setDecimals(dec)
        self._value.setValue(default)
        form.addRow(label + ":", self._value)

        if metric_type == "sleep":
            self._quality = QSpinBox()
            self._quality.setRange(1, 5)
            self._quality.setValue(3)
            form.addRow("کیفیت خواب (۱-۵):", self._quality)
        else:
            self._quality = None
        layout.addLayout(form)

        btns = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.clicked.connect(self.reject)
        save = QPushButton("ذخیره")
        save.setProperty("class", "primary")
        save.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def get_value(self):
        return self._value.value(), (self._quality.value() if self._quality else None)


class WorkoutFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ثبت تمرین")
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setMinimumWidth(380)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        from ui.style.icons import icon as _icon2
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(8)
        hdr_icon_lbl = QLabel()
        hdr_icon_lbl.setPixmap(_icon2("health", 17, colors().text_primary).pixmap(17, 17))
        hdr_row.addWidget(hdr_icon_lbl)
        hdr = QLabel("ثبت تمرین")
        hdr.setStyleSheet("font-size:16px;font-weight:700;background:transparent;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        form = QFormLayout()
        self._type = QComboBox()
        self._type.addItems(["باشگاه","دویدن","یوگا","شنا","پیاده‌روی","دوچرخه‌سواری","متفرقه"])
        form.addRow("نوع تمرین:", self._type)
        self._duration = QSpinBox()
        self._duration.setRange(0, 600)
        self._duration.setValue(30)
        self._duration.setSuffix(" دقیقه")
        form.addRow("مدت:", self._duration)
        self._calories = QSpinBox()
        self._calories.setRange(0, 5000)
        self._calories.setSuffix(" کالری")
        form.addRow("کالری:", self._calories)
        self._note = QLineEdit()
        form.addRow("یادداشت:", self._note)
        layout.addLayout(form)

        btns = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.clicked.connect(self.reject)
        save = QPushButton("ذخیره")
        save.setProperty("class", "primary")
        save.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def get_data(self):
        return {
            "type_": self._type.currentText(),
            "duration_min": self._duration.value(),
            "calories": self._calories.value() or None,
            "note": self._note.text().strip() or None,
        }


class HealthPage(BasePage):
    """View خالص — بدون import مستقیم از core.services؛ همه چیز از طریق
    self._vm (HealthViewModel)."""

    def setup_ui(self):
        self._vm = HealthViewModel(self)
        self._vm.today_changed.connect(self._on_today_changed)
        self._vm.workouts_changed.connect(self._on_workouts_changed)
        self._vm.error_occurred.connect(self._show_error)

        self.set_header("سلامت", "ردیابی وزن، آب، خواب و تمرینات")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        self._inner_layout = QVBoxLayout(inner)
        self._inner_layout.setSpacing(20)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(inner)
        self._content_layout.addWidget(scroll)

        # Quick log row
        quick_row = QHBoxLayout()
        quick_row.setSpacing(12)
        tc = colors()
        self._weight_card = self._make_quick_card("scale",   "وزن", "weight", tc.primary)
        self._water_card  = self._make_quick_card("droplet", "آب",  "water",  tc.info)
        self._sleep_card  = self._make_quick_card("moon",    "خواب", "sleep", tc.accent_purple)
        quick_row.addWidget(self._weight_card)
        quick_row.addWidget(self._water_card)
        quick_row.addWidget(self._sleep_card)
        self._inner_layout.addLayout(quick_row)

        # Workout section
        workout_hdr = QHBoxLayout()
        workout_hdr.setSpacing(6)
        from ui.style.icons import icon as _icon4
        w_icon_lbl = QLabel()
        w_icon_lbl.setPixmap(_icon4("health", 14, colors().text_secondary).pixmap(14, 14))
        workout_hdr.addWidget(w_icon_lbl)
        wlbl = QLabel("تمرینات اخیر")
        wlbl.setStyleSheet("font-size:15px;font-weight:600;background:transparent;")
        workout_hdr.addWidget(wlbl)
        workout_hdr.addStretch()
        add_workout_btn = QPushButton("+ تمرین جدید")
        add_workout_btn.setProperty("class", "primary")
        add_workout_btn.clicked.connect(self._add_workout)
        workout_hdr.addWidget(add_workout_btn)
        self._inner_layout.addLayout(workout_hdr)

        self._workout_list = QListWidget()
        self._workout_list.setFrameShape(QFrame.Shape.NoFrame)
        self._workout_list.setMinimumHeight(200)
        self._inner_layout.addWidget(self._workout_list)
        self._inner_layout.addStretch()

        self.refresh()

    def _make_quick_card(self, icon, label, metric_type, color):
        card = QFrame()
        card.setProperty("class", "card")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        top = QHBoxLayout()
        from ui.style.icons import icon as _icon3
        icon_lbl = QLabel()
        icon_lbl.setPixmap(_icon3(icon, 22, color).pixmap(22, 22))
        top.addWidget(icon_lbl)
        top.addStretch()
        btn = QPushButton("+")
        btn.setProperty("class", "icon")
        btn.clicked.connect(lambda: self._quick_log(metric_type))
        top.addWidget(btn)
        layout.addLayout(top)
        title_lbl = QLabel(label)
        title_lbl.setStyleSheet(f"font-size:13px;color:{colors().text_secondary};background:transparent;")
        layout.addWidget(title_lbl)
        value_lbl = QLabel("—")
        value_lbl.setObjectName(f"value_{metric_type}")
        value_lbl.setStyleSheet(f"font-size:24px;font-weight:700;color:{color};background:transparent;")
        layout.addWidget(value_lbl)
        setattr(self, f"_{metric_type}_value_lbl", value_lbl)
        card.mousePressEvent = lambda e, mt=metric_type: self._quick_log(mt)
        return card

    def _quick_log(self, metric_type: str):
        dlg = QuickLogDialog(self, metric_type)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            value, quality = dlg.get_value()
            if metric_type == "weight":
                self._vm.log_weight(value)
            elif metric_type == "water":
                self._vm.log_water(int(value))
            elif metric_type == "sleep":
                self._vm.log_sleep(value, quality)

    def _open_form(self, *args, **kwargs):
        self._add_workout()

    def _add_workout(self):
        dlg = WorkoutFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._vm.log_workout(**data)

    def refresh(self):
        self._vm.load()

    def _on_today_changed(self, today_data: dict):
        w = today_data.get("weight")
        self._weight_value_lbl.setText(f"{w} kg" if w else "—")
        water = today_data.get("water")
        self._water_value_lbl.setText(f"{int(water)} لیوان" if water else "—")
        sleep = today_data.get("sleep_hours")
        self._sleep_value_lbl.setText(f"{sleep} ساعت" if sleep else "—")

    def _on_workouts_changed(self, workouts: list):
        from ui.style.icons import icon as _icon5
        self._workout_list.clear()
        for w_ in workouts:
            date_fa = format_jalali(iso_str=w_["date"], fmt="short")
            dur = f"{w_['duration_min']} دقیقه" if w_.get("duration_min") else ""
            cal = f"  ·  {w_['calories']} کالری" if w_.get("calories") else ""
            item = QListWidgetItem(f"  {date_fa}  ·  {w_['type']}  ·  {dur}{cal}")
            item.setIcon(_icon5("health", 13, colors().text_secondary))
            self._workout_list.addItem(item)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
