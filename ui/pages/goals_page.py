"""ui/pages/goals_page.py — صفحه مدیریت اهداف."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton, QLineEdit, QComboBox, QDialog,
    QFormLayout, QTextEdit, QSpinBox, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QSplitter,
    QDoubleSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from ui.pages.base_page import BasePage
from ui.viewmodels.goal_list_viewmodel import GoalListViewModel
from ui.components.empty_state import EmptyState
from ui.components.confirm_dialog import confirm
from ui.style.theme_manager import colors, horizon_color
from ui.components.progress import CircularProgress
from ui.components.base_dialog import BaseDialog
from utils.date_utils import format_jalali, parse_jalali_input, today_iso
import config


class GoalFormDialog(QDialog):
    def __init__(self, parent=None, goal=None, parent_goal=None):
        super().__init__(parent)
        self.setWindowTitle("هدف جدید" if not goal else "ویرایش هدف")
        self.setMinimumWidth(480)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self._goal = goal
        self._parent_goal = parent_goal
        self._setup_ui()
        if goal:
            self._populate(goal)

    def _setup_ui(self):
        from ui.style.icons import icon as _icon
        c = colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(8)
        hdr_icon_lbl = QLabel()
        hdr_icon_lbl.setPixmap(_icon("target", 18, c.text_primary).pixmap(18, 18))
        hdr_row.addWidget(hdr_icon_lbl)
        hdr = QLabel(self.windowTitle())
        hdr.setStyleSheet("font-size:17px;font-weight:700;background:transparent;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._title = QLineEdit()
        self._title.setPlaceholderText("عنوان هدف را وارد کنید")
        form.addRow("عنوان *:", self._title)

        self._horizon = QComboBox()
        for k, v in config.HORIZON_LABELS.items():
            self._horizon.addItem(v, k)
        if self._parent_goal:
            self._horizon.setCurrentIndex(2)
        form.addRow("افق زمانی *:", self._horizon)

        self._desc = QTextEdit()
        self._desc.setPlaceholderText("توضیحات (اختیاری)")
        self._desc.setMaximumHeight(80)
        form.addRow("توضیحات:", self._desc)

        self._start = QLineEdit()
        self._start.setPlaceholderText("مثال: ۱۴۰۳/۰۱/۰۱")
        form.addRow("تاریخ شروع:", self._start)

        self._target = QLineEdit()
        self._target.setPlaceholderText("مثال: ۱۴۰۳/۱۲/۲۹")
        form.addRow("تاریخ پایان:", self._target)

        self._progress_mode = QComboBox()
        self._progress_mode.addItem("خودکار (از تسک‌ها و KR)", "auto")
        self._progress_mode.addItem("دستی", "manual")
        form.addRow("محاسبه پیشرفت:", self._progress_mode)

        self._manual_prog = QSpinBox()
        self._manual_prog.setRange(0, 100)
        self._manual_prog.setSuffix(" %")
        self._manual_prog.setVisible(False)
        self._progress_mode.currentIndexChanged.connect(
            lambda i: self._manual_prog.setVisible(i == 1))
        form.addRow("پیشرفت دستی:", self._manual_prog)

        layout.addLayout(form)

        btns = QHBoxLayout()
        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        self._save_btn = QPushButton("ذخیره")
        self._save_btn.setProperty("class", "primary")
        self._save_btn.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(self._save_btn)
        layout.addLayout(btns)

    def _populate(self, goal):
        self._title.setText(goal.title)
        idx = self._horizon.findData(goal.horizon.value)
        if idx >= 0:
            self._horizon.setCurrentIndex(idx)
        if goal.description:
            self._desc.setPlainText(goal.description)
        if goal.start_date:
            self._start.setText(format_jalali(iso_str=goal.start_date))
        if goal.target_date:
            self._target.setText(format_jalali(iso_str=goal.target_date))
        idx2 = self._progress_mode.findData(goal.progress_mode.value)
        if idx2 >= 0:
            self._progress_mode.setCurrentIndex(idx2)
        self._manual_prog.setValue(int(goal.manual_progress))

    def _save(self):
        if not self._title.text().strip():
            self._title.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        data = {
            "title":         self._title.text().strip(),
            "horizon":       self._horizon.currentData(),
            "description":   self._desc.toPlainText().strip() or None,
            "progress_mode": self._progress_mode.currentData(),
            "manual_progress": self._manual_prog.value(),
        }
        s = parse_jalali_input(self._start.text())
        if s:
            data["start_date"] = s.isoformat()
        t = parse_jalali_input(self._target.text())
        if t:
            data["target_date"] = t.isoformat()
        if self._parent_goal:
            data["parent_goal_id"] = self._parent_goal.id
        return data


class MilestonesDialog(BaseDialog):
    """دیالوگ مدیریت نقاط عطف (Key Results) یک هدف.

    طبق بخش ۴ اسپک: "Goals: ... milestones" — این قابلیت قبلاً کامل در
    لایه‌ی backend وجود داشت (core.services.goal_service.get_key_results
    و غیره) اما هیچ UI ای برایش ساخته نشده بود.

    Signals:
        milestone_saved(int, dict): goal_id، داده‌ی نقطه‌ی عطف (شامل id
            اگر ویرایش باشد).
        milestone_removed(int, int): kr_id، goal_id.
    """

    milestone_saved = Signal(int, dict)
    milestone_removed = Signal(int, int)

    def __init__(self, parent, goal, milestones: list):
        super().__init__(f"نقاط عطف — {goal.title}", parent, min_width=440)
        self.goal = goal
        self._milestones = milestones

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(8)
        self.body.addLayout(self._rows_layout)
        self._render_rows()

        add_row = QHBoxLayout()
        self._new_title = QLineEdit()
        self._new_title.setPlaceholderText("عنوان نقطه‌ی عطف جدید")
        self._new_target = QDoubleSpinBox()
        self._new_target.setRange(1, 1_000_000)
        self._new_target.setValue(1)
        self._new_target.setFixedWidth(90)
        add_btn = QPushButton("+ افزودن")
        add_btn.setProperty("class", "primary")
        add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self._new_title, 1)
        add_row.addWidget(self._new_target)
        add_row.addWidget(add_btn)
        self.body.addLayout(add_row)

        close_btn = QPushButton("بستن")
        close_btn.setProperty("class", "secondary")
        close_btn.clicked.connect(self.accept)
        self.body.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignLeft)

    def update_milestones(self, milestones: list) -> None:
        """بعد از هر save/remove async، از بیرون (GoalsPage) صدا زده
        می‌شود تا لیست نمایش‌داده‌شده تازه بماند — دیالوگ مودال است ولی
        چون exec() یک event loop تودرتو اجراست، سیگنال‌های async هنوز
        در همین حین می‌رسند."""
        self._milestones = milestones
        self._render_rows()

    def _render_rows(self):
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        c = colors()
        if not self._milestones:
            lbl = QLabel("هنوز نقطه‌ی عطفی ثبت نشده.")
            lbl.setStyleSheet(f"color:{c.text_secondary};background:transparent;font-size:12px;")
            self._rows_layout.addWidget(lbl)
            return

        from ui.style.icons import icon as _icon
        for kr in self._milestones:
            row = QHBoxLayout()
            done = kr.current >= kr.target
            status_lbl = QLabel()
            status_lbl.setPixmap(_icon("check" if done else "empty", 13,
                                       c.success if done else c.text_disabled).pixmap(13, 13))
            row.addWidget(status_lbl)
            title_lbl = QLabel(kr.title)
            title_lbl.setStyleSheet("background:transparent;font-size:13px;")
            row.addWidget(title_lbl, 1)

            unit_suffix = f" {kr.unit}" if kr.unit else ""
            progress_lbl = QLabel(f"{kr.current:g}/{kr.target:g}{unit_suffix}")
            progress_lbl.setStyleSheet(f"color:{c.text_secondary};background:transparent;font-size:11px;")
            row.addWidget(progress_lbl)

            toggle_btn = QPushButton()
            toggle_btn.setIcon(_icon("undo" if done else "check", 13, c.text_secondary))
            toggle_btn.setProperty("class", "icon")
            toggle_btn.setToolTip("بازگردانی" if done else "علامت‌زدن به‌عنوان انجام‌شده")
            toggle_btn.clicked.connect(lambda _c=False, k=kr: self._toggle(k))
            row.addWidget(toggle_btn)

            del_btn = QPushButton()
            del_btn.setIcon(_icon("trash", 13, c.danger))
            del_btn.setProperty("class", "icon")
            del_btn.clicked.connect(lambda _c=False, k=kr: self.milestone_removed.emit(k.id, self.goal.id))
            row.addWidget(del_btn)

            self._rows_layout.addLayout(row)

    def _toggle(self, kr) -> None:
        new_current = 0 if kr.current >= kr.target else kr.target
        self.milestone_saved.emit(self.goal.id, {
            "kr_id": kr.id, "title": kr.title, "target": kr.target,
            "current": new_current, "unit": kr.unit,
        })

    def _on_add(self) -> None:
        title = self._new_title.text().strip()
        if not title:
            return
        self.milestone_saved.emit(self.goal.id, {
            "title": title, "target": self._new_target.value(), "current": 0,
        })
        self._new_title.clear()
        self._new_target.setValue(1)


class GoalCard(QFrame):
    edit_requested   = Signal(object)
    delete_requested = Signal(object)
    add_sub_requested = Signal(object)
    milestones_requested = Signal(object)

    def __init__(self, goal, parent=None):
        super().__init__(parent)
        self.goal = goal
        self.setProperty("class", "card")
        self.setMinimumHeight(110)
        self._catchup_lbl = None
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 14)
        outer.setSpacing(8)

        top = QHBoxLayout()
        tc = colors()
        horizon_badge = QLabel(config.HORIZON_LABELS.get(
            self.goal.horizon.value, self.goal.horizon.value))
        color = horizon_color(self.goal.horizon.value)
        horizon_badge.setStyleSheet(f"""
            background:{color}22; color:{color};
            border-radius:10px; padding:2px 10px; font-size:11px; font-weight:600;
        """)
        top.addWidget(horizon_badge)
        top.addStretch()

        from ui.style.icons import icon as _icon
        edit_btn = QPushButton()
        edit_btn.setIcon(_icon("edit", 13, tc.text_secondary))
        edit_btn.setProperty("class", "icon")
        edit_btn.setToolTip("ویرایش")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.goal))
        milestones_btn = QPushButton()
        milestones_btn.setIcon(_icon("target", 13, tc.text_secondary))
        milestones_btn.setProperty("class", "icon")
        milestones_btn.setToolTip("نقاط عطف")
        milestones_btn.clicked.connect(lambda: self.milestones_requested.emit(self.goal))
        add_sub_btn = QPushButton()
        add_sub_btn.setIcon(_icon("add", 13, tc.text_secondary))
        add_sub_btn.setProperty("class", "icon")
        add_sub_btn.setToolTip("افزودن زیرهدف")
        add_sub_btn.clicked.connect(lambda: self.add_sub_requested.emit(self.goal))
        del_btn = QPushButton()
        del_btn.setIcon(_icon("trash", 13, tc.danger))
        del_btn.setProperty("class", "icon")
        del_btn.setToolTip("حذف")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.goal))
        for b in [edit_btn, milestones_btn, add_sub_btn, del_btn]:
            top.addWidget(b)
        outer.addLayout(top)

        # ردیف اصلی: ring پیشرفت در کنار محتوای متنی (Phase 5 — جایگزین
        # نوار خطی قبلی، طبق بخش ۴ اسپک: "Goals: Progress ring")
        main_row = QHBoxLayout()
        main_row.setSpacing(14)

        prog = int(self.goal.computed_progress)
        ring = CircularProgress(value=prog, size=56, thickness=5, accent=color)
        main_row.addWidget(ring, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        title_lbl = QLabel(self.goal.title)
        title_lbl.setStyleSheet("font-size:15px;font-weight:600;background:transparent;")
        title_lbl.setWordWrap(True)
        text_col.addWidget(title_lbl)

        if self.goal.description:
            desc = QLabel(self.goal.description)
            desc.setStyleSheet(f"font-size:12px;color:{tc.text_secondary};background:transparent;")
            desc.setWordWrap(True)
            text_col.addWidget(desc)

        if self.goal.target_date:
            from utils.date_utils import days_until, format_jalali
            days = days_until(self.goal.target_date)
            date_str = format_jalali(iso_str=self.goal.target_date, fmt="named")
            color2 = tc.danger if days < 0 else tc.warning if days < 14 else tc.text_secondary
            date_lbl = QLabel(f"{date_str}" + (f"  ({abs(days)} روز {'مانده' if days>=0 else 'گذشته'})" if days is not None else ""))
            date_lbl.setStyleSheet(f"font-size:11px;color:{color2};background:transparent;")
            text_col.addWidget(date_lbl)

        main_row.addLayout(text_col, 1)
        outer.addLayout(main_row)

        # بنر پلن جبران عقب‌ماندگی (Phase 5) — پیش‌فرض مخفی، فقط وقتی
        # ViewModel محاسبه کند که این هدف عقب‌افتاده است نمایش داده می‌شود
        self._catchup_lbl = QLabel("")
        self._catchup_lbl.setWordWrap(True)
        self._catchup_lbl.setStyleSheet(f"""
            background:{tc.warning}18; color:{tc.warning};
            border-radius:6px; padding:6px 10px; font-size:11px;
        """)
        self._catchup_lbl.setVisible(False)
        outer.addWidget(self._catchup_lbl)

    def set_catchup_plan(self, plan_text: str) -> None:
        if self._catchup_lbl:
            self._catchup_lbl.setText(plan_text)
            self._catchup_lbl.setVisible(True)


class GoalsPage(BasePage):
    """View خالص — بدون import مستقیم از core.services؛ همه چیز از طریق
    self._vm (GoalListViewModel)."""

    def setup_ui(self):
        self._vm = GoalListViewModel(self)
        self._vm.goals_changed.connect(self._on_goals_changed)
        self._vm.catchup_plans_changed.connect(self._on_catchup_plans_changed)
        self._vm.milestones_loaded.connect(self._on_milestones_loaded)
        self._vm.loading_changed.connect(self._on_loading_changed)
        self._vm.error_occurred.connect(self._show_error)
        self._goal_cards = {}          # goal_id -> GoalCard (برای بنر catch-up)
        self._open_milestones_dialog = None

        self.set_header("اهداف", "مدیریت چشم‌انداز، اهداف سالانه و فصلی")
        self._add_btn = self.add_header_action("+ هدف جدید")
        self._add_btn.clicked.connect(lambda: self._open_form())

        tabs = QTabWidget()
        self._content_layout.addWidget(tabs)

        for horizon, label in config.HORIZON_LABELS.items():
            tab = QScrollArea()
            tab.setWidgetResizable(True)
            tab.setFrameShape(QFrame.Shape.NoFrame)
            inner = QWidget()
            setattr(self, f"_layout_{horizon}", QVBoxLayout(inner))
            getattr(self, f"_layout_{horizon}").setSpacing(12)
            getattr(self, f"_layout_{horizon}").setContentsMargins(0, 0, 0, 0)
            getattr(self, f"_layout_{horizon}").addStretch()
            tab.setWidget(inner)
            tabs.addTab(tab, label)

        self._tabs = tabs
        self.refresh()

    def refresh(self):
        self._vm.load()

    def _on_loading_changed(self, is_loading: bool):
        self._add_btn.setEnabled(not is_loading)

    def _on_goals_changed(self, goals: list):
        for horizon in config.HORIZON_LABELS:
            lyt = getattr(self, f"_layout_{horizon}")
            while lyt.count() > 1:
                item = lyt.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        self._goal_cards = {}

        for goal in goals:
            h = goal.horizon.value
            lyt = getattr(self, f"_layout_{h}", None)
            if not lyt:
                continue
            card = GoalCard(goal)
            card.edit_requested.connect(self._open_form)
            card.delete_requested.connect(self._delete)
            card.add_sub_requested.connect(lambda g: self._open_form(parent_goal=g))
            card.milestones_requested.connect(self._open_milestones)
            lyt.insertWidget(lyt.count() - 1, card)
            self._goal_cards[goal.id] = card

    def _on_catchup_plans_changed(self, plans: dict):
        """طبق بخش ۴ اسپک: "catch-up plan generation" — بنر هشدار را
        فقط روی کارت اهدافی که واقعاً عقب‌افتاده‌اند نشان می‌دهد."""
        for goal_id, plan_text in plans.items():
            card = self._goal_cards.get(goal_id)
            if card:
                card.set_catchup_plan(plan_text)

    def _open_milestones(self, goal):
        self._open_milestones_dialog = MilestonesDialog(self, goal, [])
        self._open_milestones_dialog.milestone_saved.connect(
            lambda goal_id, data: self._vm.save_milestone(goal_id, **data))
        self._open_milestones_dialog.milestone_removed.connect(self._vm.remove_milestone)
        self._vm.load_milestones(goal.id)
        self._open_milestones_dialog.exec()
        self._open_milestones_dialog = None

    def _on_milestones_loaded(self, goal_id: int, milestones: list):
        if (self._open_milestones_dialog is not None
                and self._open_milestones_dialog.goal.id == goal_id):
            self._open_milestones_dialog.update_milestones(milestones)

    def _open_form(self, goal=None, parent_goal=None):
        dlg = GoalFormDialog(self, goal, parent_goal)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if goal:
                self._vm.update(goal.id, **data)
            else:
                self._vm.create(**data)

    def _delete(self, goal):
        if confirm(self, "حذف هدف", f"آیا از حذف «{goal.title}» مطمئن هستید؟",
                   "حذف", danger=True):
            self._vm.remove(goal.id)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
