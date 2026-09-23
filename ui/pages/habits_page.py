"""ui/pages/habits_page.py — صفحه عادت‌ها."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton, QLineEdit, QComboBox, QDialog,
    QFormLayout, QGridLayout, QSizePolicy, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QDate
from ui.pages.base_page import BasePage
from ui.components.empty_state import EmptyState
from ui.components.confirm_dialog import confirm
from ui.style.theme_manager import colors
from ui.viewmodels.habit_list_viewmodel import HabitListViewModel
from ui.components.heatmap import HabitHeatmap
from ui.components.toast import show_toast
from ui.components.confetti import ConfettiOverlay
import config


class HabitFormDialog(QDialog):
    def __init__(self, parent=None, habit=None):
        super().__init__(parent)
        self.setWindowTitle("عادت جدید" if not habit else "ویرایش عادت")
        self.setMinimumWidth(420)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self._habit = habit
        self._setup_ui()
        if habit:
            self._populate(habit)

    def _setup_ui(self):
        from ui.style.icons import icon as _icon2
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(8)
        hdr_icon_lbl = QLabel()
        hdr_icon_lbl.setPixmap(_icon2("flame", 18, colors().warning).pixmap(18, 18))
        hdr_row.addWidget(hdr_icon_lbl)
        hdr = QLabel(self.windowTitle())
        hdr.setStyleSheet("font-size:17px;font-weight:700;background:transparent;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name = QLineEdit()
        self._name.setPlaceholderText("نام عادت")
        form.addRow("نام *:", self._name)

        icon_row = QHBoxLayout()
        self._icon = QLineEdit()
        self._icon.setPlaceholderText("⭐")
        self._icon.setMaximumWidth(60)
        icons = ["⭐", "💪", "📚", "🏃", "💧", "🧘", "✍️", "🎯", "💊", "🥗"]
        for ic in icons:
            b = QPushButton(ic)
            b.setProperty("class", "ghost")
            b.setFixedSize(32, 32)
            b.clicked.connect(lambda _, i=ic: self._icon.setText(i))
            icon_row.addWidget(b)
        icon_row.addStretch()
        form.addRow("آیکون:", self._icon)
        layout.addLayout(form)
        layout.addLayout(icon_row)

        form2 = QFormLayout()
        form2.setSpacing(10)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._color = QLineEdit()
        self._color.setPlaceholderText(colors().success)
        self._color.setText(colors().success)
        form2.addRow("رنگ:", self._color)

        self._category = QComboBox()
        for cat in ["سلامت", "یادگیری", "ذهنی", "روابط", "کاری", "متفرقه"]:
            self._category.addItem(cat)
        form2.addRow("دسته‌بندی:", self._category)

        layout.addLayout(form2)

        btns = QHBoxLayout()
        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("ذخیره")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _populate(self, habit):
        self._name.setText(habit.name)
        self._icon.setText(habit.icon)
        self._color.setText(habit.color)
        idx = self._category.findText(habit.category or "متفرقه")
        if idx >= 0:
            self._category.setCurrentIndex(idx)

    def _save(self):
        if not self._name.text().strip():
            self._name.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name":     self._name.text().strip(),
            "icon":     self._icon.text().strip() or "⭐",
            "color":    self._color.text().strip() or colors().success,
            "category": self._category.currentText(),
        }


class HabitCard(QFrame):
    toggled       = Signal(int)
    edit_requested = Signal(object)
    delete_requested = Signal(object)

    def __init__(self, habit, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.setProperty("class", "card")
        self._heatmap: HabitHeatmap = None
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        layout = QHBoxLayout()
        layout.setSpacing(14)

        # Toggle button
        from ui.style.icons import icon as _icon3
        self._check_btn = QPushButton(
            "" if self.habit.logged_today else self.habit.icon)
        color = self.habit.color
        if self.habit.logged_today:
            self._check_btn.setIcon(_icon3("check", 18, "white"))
            self._check_btn.setStyleSheet(f"""
                QPushButton{{background:{color};color:white;border:none;
                border-radius:22px;font-size:16px;font-weight:700;
                min-width:44px;max-width:44px;min-height:44px;max-height:44px;}}
            """)
        else:
            self._check_btn.setStyleSheet(f"""
                QPushButton{{background:transparent;color:{color};
                border:2px solid {color};border-radius:22px;font-size:18px;
                min-width:44px;max-width:44px;min-height:44px;max-height:44px;}}
                QPushButton:hover{{background:{color}22;}}
            """)
        self._check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._check_btn.clicked.connect(lambda: self.toggled.emit(self.habit.id))
        layout.addWidget(self._check_btn)

        info = QVBoxLayout()
        info.setSpacing(3)
        name_lbl = QLabel(self.habit.name)
        name_lbl.setStyleSheet("font-size:14px;font-weight:600;background:transparent;")
        info.addWidget(name_lbl)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)
        if self.habit.category:
            cat_lbl = QLabel(self.habit.category)
            cat_lbl.setStyleSheet(f"font-size:11px;color:{colors().text_secondary};background:transparent;")
            meta_row.addWidget(cat_lbl)
        streak_lbl = QLabel(f"{self.habit.current_streak} روز")
        streak_lbl.setStyleSheet(f"font-size:11px;color:{color};font-weight:600;background:transparent;")
        meta_row.addWidget(streak_lbl)
        meta_row.addStretch()
        info.addLayout(meta_row)
        layout.addLayout(info)
        layout.addStretch()

        # GitHub-style heatmap (Phase 5) — داده‌اش بعداً async از
        # HabitListViewModel می‌رسد؛ اول با دیکشنری خالی ساخته می‌شود
        self._heatmap = HabitHeatmap(data={}, accent=color, weeks=12)
        layout.addWidget(self._heatmap)

        edit_btn = QPushButton()
        edit_btn.setIcon(_icon3("edit", 13, colors().text_secondary))
        edit_btn.setProperty("class", "icon")
        edit_btn.setToolTip("ویرایش")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.habit))
        del_btn = QPushButton()
        del_btn.setIcon(_icon3("trash", 13, colors().danger))
        del_btn.setProperty("class", "icon")
        del_btn.setToolTip("حذف")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.habit))
        layout.addWidget(edit_btn)
        layout.addWidget(del_btn)

        outer.addLayout(layout)

    def set_heatmap_data(self, data: dict) -> None:
        if self._heatmap:
            self._heatmap.set_data(data, accent=self.habit.color)


class HabitsPage(BasePage):
    """View خالص — بدون import مستقیم از core.services؛ همه چیز از طریق
    self._vm (HabitListViewModel) که عملیات را async روی Worker اجرا
    می‌کند (هرگز UI thread را بلاک نمی‌کند)."""

    def setup_ui(self):
        self._vm = HabitListViewModel(self)
        self._vm.habits_changed.connect(self._on_habits_changed)
        self._vm.stats_changed.connect(self._on_stats_changed)
        self._vm.heatmaps_changed.connect(self._on_heatmaps_changed)
        self._vm.nudge_needed.connect(self._on_nudge_needed)
        self._vm.streak_milestone_reached.connect(self._on_streak_milestone)
        self._vm.loading_changed.connect(self._on_loading_changed)
        self._vm.error_occurred.connect(self._show_error)
        self._habit_cards = {}  # habit_id -> HabitCard (برای رساندن heatmap async)

        self.set_header("عادت‌ها", "ردیابی روزانه و آمار streak")
        self._add_btn = self.add_header_action("+ عادت جدید")
        self._add_btn.clicked.connect(lambda: self._open_form())

        # Stats row
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(12)
        self._content_layout.addLayout(self._stats_row)

        # Habit list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setSpacing(10)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_widget)
        self._content_layout.addWidget(scroll)

        self.refresh()

    def refresh(self):
        self._vm.load()

    def _on_loading_changed(self, is_loading: bool):
        self._add_btn.setEnabled(not is_loading)

    def _on_stats_changed(self, stats: dict):
        while self._stats_row.count():
            item = self._stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        c = colors()
        for label, value, color in [
            ("کل عادت‌ها", str(stats.get("total", 0)), c.primary),
            ("انجام‌شده امروز", str(stats.get("done_today", 0)), c.success),
            ("باقی‌مانده", str(stats.get("pending", 0)), c.warning),
        ]:
            card = QFrame()
            card.setProperty("class", "card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            v = QLabel(value)
            v.setStyleSheet(f"font-size:26px;font-weight:700;color:{color};background:transparent;")
            l = QLabel(label)
            l.setStyleSheet(f"font-size:12px;color:{c.text_secondary};background:transparent;")
            cl.addWidget(v)
            cl.addWidget(l)
            self._stats_row.addWidget(card)
        self._stats_row.addStretch()

    def _on_habits_changed(self, habits: list):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._habit_cards = {}

        if not habits:
            empty = EmptyState("flame", "هیچ عادتی تعریف نشده",
                               "اولین عادت خود را اضافه کنید", "+ عادت جدید")
            empty.action_clicked.connect(lambda: self._open_form())
            self._list_layout.insertWidget(0, empty)
        else:
            for h in habits:
                card = HabitCard(h)
                card.toggled.connect(self._vm.toggle_today)
                card.edit_requested.connect(self._open_form)
                card.delete_requested.connect(self._delete)
                self._list_layout.insertWidget(self._list_layout.count() - 1, card)
                self._habit_cards[h.id] = card

    def _on_heatmaps_changed(self, heatmaps: dict):
        """طبق بخش ۴ اسپک: "GitHub‑style heatmap" — بعد از بارگذاری async
        داده‌ی ۱۲ هفته‌ی اخیر، به کارت مربوطه می‌رسد."""
        for habit_id, info in heatmaps.items():
            card = self._habit_cards.get(habit_id)
            if card:
                card.set_heatmap_data(info["heatmap"])

    def _on_nudge_needed(self, habit):
        """طبق بخش ۴ اسپک: "Smart nudge if missed 3 days"."""
        show_toast(
            self, f"«{habit.name}» رو ۳ روزه فراموش کردی — امروز انجامش بده!",
            duration_ms=6000, icon="clock",
        )

    def _on_streak_milestone(self, habit):
        """طبق بخش ۹ اسپک: "completion celebration (confetti for streaks)"."""
        ConfettiOverlay.celebrate(self)
        show_toast(
            self, f"{habit.current_streak} روز متوالی «{habit.name}»! فوق‌العاده‌ای!",
            duration_ms=5000, icon="award",
        )

    def _open_form(self, habit=None):
        dlg = HabitFormDialog(self, habit)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if habit:
                self._vm.update(habit.id, **data)
            else:
                self._vm.create(**data)

    def _delete(self, habit):
        if confirm(self, "حذف عادت", f"آیا از حذف «{habit.name}» مطمئن هستید؟",
                   "حذف", danger=True):
            self._vm.remove(habit.id)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
