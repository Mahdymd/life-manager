"""ui/pages/tasks_page.py — صفحه مدیریت تسک‌ها."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton, QLineEdit, QComboBox, QDialog,
    QFormLayout, QTextEdit, QCheckBox, QSpinBox, QTabWidget,
    QListWidget, QListWidgetItem, QSplitter, QSizePolicy,
    QGraphicsOpacityEffect, QGridLayout,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from ui.pages.base_page import BasePage
from ui.components.empty_state import EmptyState
from ui.components.confirm_dialog import confirm
from ui.components.skeleton_loader import SkeletonLoader
from ui.viewmodels.task_list_viewmodel import TaskListViewModel
from ui.components.toast import show_toast
from ui.components.breadcrumb import SegmentedControl
from ui.components.history_dialog import HistoryDialog
from ui.style.theme_manager import colors, Motion
from utils.date_utils import format_jalali, parse_jalali_input, today_iso, today_jalali, jalali_to_gregorian
import config


class TaskFormDialog(QDialog):
    def __init__(self, parent=None, task=None, categories=None):
        super().__init__(parent)
        self._categories = categories
        self.setWindowTitle("تسک جدید" if not task else "ویرایش تسک")
        self.setMinimumWidth(500)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self._task = task
        self._setup_ui()
        if task:
            self._populate(task)

    def _setup_ui(self):
        c = colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        from ui.style.icons import icon as _icon2
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(8)
        hdr_icon_lbl = QLabel()
        hdr_icon_lbl.setPixmap(_icon2("check", 18, c.text_primary).pixmap(18, 18))
        hdr_row.addWidget(hdr_icon_lbl)
        title_lbl = QLabel(self.windowTitle())
        title_lbl.setStyleSheet("font-size: 17px; font-weight: 700; background: transparent;")
        hdr_row.addWidget(title_lbl)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        form = QFormLayout(); form.setSpacing(12); form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.title_input = QLineEdit(); self.title_input.setPlaceholderText("عنوان تسک")
        self.desc_input  = QTextEdit(); self.desc_input.setPlaceholderText("توضیحات (اختیاری)"); self.desc_input.setMaximumHeight(80)
        self.due_input   = QLineEdit(); self.due_input.setPlaceholderText("مثال: ۱۴۰۳/۰۵/۱۲")
        self.priority_cb = QComboBox()
        from ui.style.icons import icon as _icon
        _pc = colors()
        for val, lbl, col in [
            ("urgent", "فوری", _pc.danger), ("high", "بالا", _pc.priority_high),
            ("medium", "متوسط", _pc.primary), ("low", "پایین", _pc.success),
        ]:
            self.priority_cb.addItem(_icon("dot", 14, col), lbl, val)
        self.priority_cb.setCurrentIndex(2)
        self.status_cb = QComboBox()
        for val, lbl in [("todo","انجام‌نشده"),("in_progress","در حال انجام"),("done","انجام‌شده")]:
            self.status_cb.addItem(lbl, val)
        self.recur_cb = QComboBox()
        for val, lbl in [("none","بدون تکرار"),("daily","روزانه"),("weekly","هفتگی"),("monthly","ماهانه")]:
            self.recur_cb.addItem(lbl, val)
        self.estimated_spin = QSpinBox(); self.estimated_spin.setRange(0, 480); self.estimated_spin.setSuffix(" دقیقه"); self.estimated_spin.setSpecialValueText("بدون تخمین")

        form.addRow("عنوان *", self.title_input)
        form.addRow("توضیحات", self.desc_input)
        form.addRow("سررسید (شمسی)", self.due_input)
        form.addRow("اولویت", self.priority_cb)
        form.addRow("وضعیت", self.status_cb)
        form.addRow("تکرار", self.recur_cb)
        form.addRow("تخمین زمان", self.estimated_spin)

        # Categories
        self.cat_cb = QComboBox(); self._load_categories()
        form.addRow("دسته‌بندی", self.cat_cb)
        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("انصراف"); cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("ذخیره"); save_btn.setProperty("class","primary"); save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _load_categories(self):
        self.cat_cb.addItem("بدون دسته‌بندی", None)
        if self._categories is not None:
            # داده‌ی از پیش بارگذاری‌شده توسط ViewModel (async، بدون تماس
            # مستقیم این دیالوگ با دیتابیس).
            for c in self._categories:
                self.cat_cb.addItem(c["name"], c["id"])
            return
        # Fallback via repository (never direct connection from UI layer).
        try:
            from core.repositories.tag_repository import TagRepository
            for c in TagRepository().get_category_all("task"):
                self.cat_cb.addItem(c["name"], c["id"])
        except Exception:
            pass

    def _populate(self, task):
        self.title_input.setText(task.title)
        self.desc_input.setPlainText(task.description or "")
        if task.due_date:
            self.due_input.setText(format_jalali(iso_str=task.due_date))
        for i in range(self.priority_cb.count()):
            if self.priority_cb.itemData(i) == task.priority.value:
                self.priority_cb.setCurrentIndex(i); break
        for i in range(self.status_cb.count()):
            if self.status_cb.itemData(i) == task.status.value:
                self.status_cb.setCurrentIndex(i); break
        for i in range(self.recur_cb.count()):
            if self.recur_cb.itemData(i) == task.recurrence.value:
                self.recur_cb.setCurrentIndex(i); break
        if task.estimated_min:
            self.estimated_spin.setValue(task.estimated_min)

    def _save(self):
        title = self.title_input.text().strip()
        if not title:
            self.title_input.setFocus(); self.title_input.setStyleSheet(f"border-color: {colors().danger};"); return
        self.accept()

    def get_data(self) -> dict:
        due_date = None
        raw_due = self.due_input.text().strip()
        if raw_due:
            parsed = parse_jalali_input(raw_due)
            if parsed:
                due_date = parsed.isoformat()
        cat_id = self.cat_cb.currentData()
        est = self.estimated_spin.value()
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip() or None,
            "due_date": due_date,
            "priority": self.priority_cb.currentData(),
            "status": self.status_cb.currentData(),
            "recurrence": self.recur_cb.currentData(),
            "category_id": cat_id,
            "estimated_min": est if est > 0 else None,
        }


class TaskItem(QFrame):
    completed = Signal(int)
    edited    = Signal(int)
    deleted   = Signal(int)
    add_subtask_requested = Signal(int)
    history_requested = Signal(int)

    def __init__(self, task, parent=None, indent: bool = False):
        super().__init__(parent)
        self.task = task
        self.setProperty("class", "card")
        self.setFixedHeight(64)
        self._indent = indent
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        left_margin = 40 if self._indent else 16
        layout.setContentsMargins(left_margin, 8, 16, 8)
        layout.setSpacing(12)

        c = colors()
        done = self.task.status.value == "done"
        self._check = QPushButton("" if done else "○")
        self._check.setProperty("class", "icon")
        self._check.setFont(QFont("Segoe UI", 16))
        if done:
            from ui.style.icons import icon as _icon3
            self._check.setIcon(_icon3("check", 16, c.success))
        self._check.clicked.connect(self._on_check_clicked)
        layout.addWidget(self._check)

        info = QVBoxLayout(); info.setSpacing(2)
        title_style = "font-size: 13px; font-weight: 500; background: transparent;"
        if done:
            title_style += f" text-decoration: line-through; color: {c.text_secondary};"
        t = QLabel(self.task.title); t.setStyleSheet(title_style)
        meta_parts = []
        if self.task.due_date:
            from utils.date_utils import is_overdue, is_today
            if is_overdue(self.task.due_date) and not done:
                meta_parts.append(f"<span style='color:{c.danger}'>{format_jalali(iso_str=self.task.due_date)}</span>")
            elif is_today(self.task.due_date):
                meta_parts.append(f"<span style='color:{c.warning}'>امروز</span>")
            else:
                meta_parts.append(f"{format_jalali(iso_str=self.task.due_date)}")
        if self.task.category_name:
            meta_parts.append(f"{self.task.category_name}")
        if self.task.estimated_min:
            meta_parts.append(f"{self.task.estimated_min} دقیقه")
        m = QLabel("  ·  ".join(meta_parts) if meta_parts else "")
        m.setStyleSheet(f"font-size: 11px; color: {c.text_secondary}; background: transparent;")
        m.setTextFormat(Qt.TextFormat.RichText)
        info.addWidget(t); info.addWidget(m)
        layout.addLayout(info)
        layout.addStretch()

        priority_colors = {
            "urgent": c.danger, "high": c.priority_high,
            "medium": c.primary, "low": c.success,
        }
        pc = priority_colors.get(self.task.priority.value, c.primary)
        pdot = QLabel("●"); pdot.setStyleSheet(f"color:{pc}; background:transparent; font-size:12px;")
        layout.addWidget(pdot)

        from ui.style.icons import icon as _icon4
        edit_btn = QPushButton(); edit_btn.setProperty("class","icon")
        edit_btn.setIcon(_icon4("edit", 15, c.text_secondary))
        edit_btn.setToolTip("ویرایش")
        edit_btn.clicked.connect(lambda: self.edited.emit(self.task.id))
        if not self._indent:
            add_sub_btn = QPushButton(); add_sub_btn.setProperty("class","icon")
            add_sub_btn.setIcon(_icon4("add", 15, c.text_secondary))
            add_sub_btn.setToolTip("افزودن زیرتسک")
            add_sub_btn.clicked.connect(lambda: self.add_subtask_requested.emit(self.task.id))
            layout.addWidget(add_sub_btn)
        history_btn = QPushButton(); history_btn.setProperty("class","icon")
        history_btn.setIcon(_icon4("clock", 15, c.text_secondary))
        history_btn.setToolTip("تاریخچه‌ی نسخه‌ها")
        history_btn.clicked.connect(lambda: self.history_requested.emit(self.task.id))
        layout.addWidget(history_btn)
        del_btn = QPushButton(); del_btn.setProperty("class","icon")
        del_btn.setIcon(_icon4("trash", 15, c.danger))
        del_btn.setToolTip("حذف")
        del_btn.clicked.connect(lambda: self.deleted.emit(self.task.id))
        layout.addWidget(edit_btn); layout.addWidget(del_btn)

    def _on_check_clicked(self):
        """طبق بخش ۴ اسپک: "completion animation" — فقط وقتی تسک از
        نشده به شده تغییر می‌کند (نه برعکس) یک پالس محو-ظاهر کوتاه
        پخش می‌شود، بعد سیگنال completed برای ثبت واقعی در دیتابیس
        emit می‌گردد (خودِ رفرش لیست async و بعد از این اتفاق می‌افتد)."""
        was_done = self.task.status.value == "done"
        if not was_done:
            self._play_completion_animation()
        self.completed.emit(self.task.id)

    def _play_completion_animation(self):
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(Motion.NORMAL)
        anim.setStartValue(1.0)
        anim.setKeyValueAt(0.5, 0.35)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        # نگه‌داشتن ارجاع روی خودِ ویجت تا قبل از پایان انیمیشن توسط
        # garbage collector پاک نشود
        self._completion_anim = anim
        anim.start()


class _BoardColumn(QListWidget):
    """یک ستون از نمای Kanban (بورد) که کارت تسک بین ستون‌ها با
    drag-and-drop قابل‌جابه‌جایی است.

    نکته‌ی فنی: QListWidget به‌طور پیش‌فرض بین دو نمونه‌ی جدا از هم
    (دو ستون مختلف) آیتم را با فرمت MIME داخلی Qt منتقل می‌کند که
    task_id را در خود ندارد؛ برای همین mimeData/dropEvent را override
    می‌کنیم تا صریحاً شناسه‌ی تسک منتقل شود.

    Signals:
        task_dropped(int): task_id ی که در این ستون رها شده (باید
            status اش به status_value این ستون تغییر کند).
    """

    task_dropped = Signal(int)

    def __init__(self, status_value: str, parent=None):
        super().__init__(parent)
        self.status_value = status_value
        self.setDragDropMode(QListWidget.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def mimeData(self, items):
        from PySide6.QtCore import QMimeData
        mime = QMimeData()
        if items:
            task_id = items[0].data(Qt.ItemDataRole.UserRole)
            mime.setText(str(task_id))
        return mime

    def dropEvent(self, event):
        task_id_text = event.mimeData().text()
        if task_id_text.isdigit():
            event.acceptProposedAction()
            self.task_dropped.emit(int(task_id_text))
        else:
            event.ignore()


class TasksPage(BasePage):
    """
    View خالص — هیچ import مستقیمی از core.services/core.repositories ندارد.
    تمام state و منطق async از طریق self._vm (TaskListViewModel) است.
    این صفحه فقط: (۱) رویدادهای کاربر را به متدهای ViewModel ترجمه می‌کند
    و (۲) signal های ViewModel را به رندر UI ترجمه می‌کند.
    """

    def setup_ui(self):
        self._suppress_next_undo_toast = False
        self._first_load_done = False
        self._view_mode = "list"
        self._skeleton = None
        self._vm = TaskListViewModel(self)
        self._vm.tasks_changed.connect(self._on_tasks_changed)
        self._vm.stats_changed.connect(self._on_stats_changed)
        self._vm.loading_changed.connect(self._on_loading_changed)
        self._vm.error_occurred.connect(self._show_error)
        self._vm.undo_performed.connect(self._on_undo_performed)
        self._vm.undo_available_changed.connect(self._on_undo_available_changed)
        self._vm.categories_changed.connect(self._on_categories_changed)
        self._vm.subtasks_changed.connect(self._on_subtasks_changed)
        self._vm.history_loaded.connect(self._on_history_loaded)
        self._subtasks_map = {}
        self._last_tasks = None
        self._categories_cache = []

        # میان‌بر Ctrl+Z برای بازگردانی آخرین اقدام (طبق بخش ۱۲ اسپک:
        # "Ctrl+Z (undo)"). چون فقط زمانی معنی دارد که این صفحه فعال/
        # قابل‌مشاهده باشد، shortcut context را به همین widget محدود می‌کنیم.
        self._undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self._undo_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._undo_shortcut.activated.connect(self._vm.undo_last)

        self.set_header("تسک‌ها", "مدیریت کارها و فعالیت‌ها")
        self._new_btn = self.add_header_action("+ تسک جدید", "primary")
        self._new_btn.clicked.connect(self._open_new_dialog)

        # افزودن سریع (inline) — طبق بخش ۴ اسپک: "Tasks: ... inline
        # creation". فقط عنوان می‌گیرد؛ برای جزئیات کامل (اولویت،
        # تاریخ، ...) همچنان دیالوگ «+ تسک جدید» در دسترس است.
        quick_add_row = QHBoxLayout(); quick_add_row.setSpacing(8)
        from ui.style.icons import icon as _icon5
        self._quick_add_input = QLineEdit()
        self._quick_add_input.setPlaceholderText("افزودن سریع تسک... (Enter برای ثبت)")
        self._quick_add_input.addAction(_icon5("add", 15, colors().text_secondary),
                                        QLineEdit.ActionPosition.LeadingPosition)
        self._quick_add_input.returnPressed.connect(self._on_quick_add)
        quick_add_row.addWidget(self._quick_add_input)
        self._content_layout.addLayout(quick_add_row)

        # فیلترها
        filter_row = QHBoxLayout(); filter_row.setSpacing(10)
        self._search_input = QLineEdit(); self._search_input.setPlaceholderText("جستجو...")
        self._search_input.addAction(_icon5("search", 15, colors().text_secondary),
                                     QLineEdit.ActionPosition.LeadingPosition)
        self._search_input.setFixedWidth(200)
        self._search_input.textChanged.connect(self._on_search)
        self._filter_status = QComboBox()
        for v,l in [("","همه"),("todo","انجام‌نشده"),("in_progress","در حال انجام"),
                    ("done","انجام‌شده"),("overdue","معوقه"),("today","امروز")]:
            self._filter_status.addItem(l, v)
        self._filter_status.currentIndexChanged.connect(self._on_filters_changed)
        self._filter_priority = QComboBox()
        for v,l in [("","همه اولویت‌ها"),("urgent","فوری"),("high","بالا"),
                    ("medium","متوسط"),("low","پایین")]:
            self._filter_priority.addItem(l, v)
        self._filter_priority.currentIndexChanged.connect(self._on_filters_changed)
        self._view_toggle = SegmentedControl([("list", "≡ لیست"), ("board", "▦ بورد"), ("calendar", "تقویم")])
        self._view_toggle.value_changed.connect(self._on_view_mode_changed)
        filter_row.addWidget(self._search_input)
        filter_row.addWidget(self._filter_status)
        filter_row.addWidget(self._filter_priority)
        filter_row.addStretch()
        filter_row.addWidget(self._view_toggle)
        self._content_layout.addLayout(filter_row)

        # آمار سریع
        stats_row = QHBoxLayout(); stats_row.setSpacing(12)
        from ui.components.stat_card import MiniStatCard
        c = colors()
        self._sc_total   = MiniStatCard("کل تسک‌ها", "–")
        self._sc_today   = MiniStatCard("امروز", "–", c.warning)
        self._sc_overdue = MiniStatCard("معوقه", "–", c.danger)
        self._sc_done    = MiniStatCard("انجام‌شده", "–", c.success)
        for sc in [self._sc_total, self._sc_today, self._sc_overdue, self._sc_done]:
            stats_row.addWidget(sc)
        self._content_layout.addLayout(stats_row)

        # لیست تسک‌ها
        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setSpacing(8)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._list_widget)
        self._content_layout.addWidget(self._scroll)

        # نمای بورد (Kanban) — طبق بخش ۴ اسپک: "Tasks: List/board/
        # calendar views ... drag-and-drop"
        self._board_widget = QWidget()
        board_layout = QHBoxLayout(self._board_widget)
        board_layout.setSpacing(12)
        board_layout.setContentsMargins(0, 0, 0, 0)
        self._board_columns = {}
        for status_value, label in [("todo", "انجام‌نشده"),
                                      ("in_progress", "در حال انجام"),
                                      ("done", "انجام‌شده")]:
            col_container = QVBoxLayout()
            col_title = QLabel(label)
            col_title.setStyleSheet("font-size:13px;font-weight:600;background:transparent;")
            col_container.addWidget(col_title)
            column = _BoardColumn(status_value)
            column.setSpacing(6)
            column.task_dropped.connect(self._on_task_dropped_on_column)
            col_container.addWidget(column)
            board_layout.addLayout(col_container)
            self._board_columns[status_value] = column
        self._board_widget.setVisible(False)
        self._content_layout.addWidget(self._board_widget)

        # نمای تقویم — طبق بخش ۴ اسپک. از همان داده‌ی نمای لیست
        # (self._last_tasks) استفاده می‌کند، بدون کوئری جداگانه.
        self._cal_year, self._cal_month, _ = today_jalali()
        self._calendar_widget = QWidget()
        cal_outer = QVBoxLayout(self._calendar_widget)
        cal_outer.setContentsMargins(0, 0, 0, 0)
        cal_outer.setSpacing(10)

        cal_nav = QHBoxLayout()
        self._cal_prev_btn = QPushButton("‹"); self._cal_prev_btn.setProperty("class", "icon")
        self._cal_prev_btn.clicked.connect(self._cal_prev_month)
        self._cal_month_lbl = QLabel(); self._cal_month_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cal_month_lbl.setStyleSheet("font-size:14px;font-weight:600;background:transparent;")
        self._cal_next_btn = QPushButton("›"); self._cal_next_btn.setProperty("class", "icon")
        self._cal_next_btn.clicked.connect(self._cal_next_month)
        cal_nav.addWidget(self._cal_prev_btn)
        cal_nav.addWidget(self._cal_month_lbl, 1)
        cal_nav.addWidget(self._cal_next_btn)
        cal_outer.addLayout(cal_nav)

        self._cal_grid = QGridLayout()
        self._cal_grid.setSpacing(4)
        cal_outer.addLayout(self._cal_grid)
        cal_outer.addStretch()

        self._calendar_widget.setVisible(False)
        self._content_layout.addWidget(self._calendar_widget)

        self._search_timer = QTimer(self); self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(
            lambda: self._vm.set_search(self._search_input.text()))

        self.refresh()
        self._vm.load_categories()

    # ------------------------------------------------------------------ #
    # ترجمه‌ی رویداد کاربر → دستور به ViewModel (بدون منطق business اینجا)
    # ------------------------------------------------------------------ #
    def _on_search(self):
        self._search_timer.start(300)

    def _on_filters_changed(self):
        self._vm.set_status_filter(self._filter_status.currentData())
        self._vm.set_priority_filter(self._filter_priority.currentData())

    def refresh(self):
        """نقطه‌ی ورود عمومی (مثلاً وقتی صفحه دوباره نمایش داده می‌شود)."""
        self._vm.load()

    # ------------------------------------------------------------------ #
    # ترجمه‌ی signal های ViewModel → رندر UI (بدون فراخوانی مستقیم سرویس)
    # ------------------------------------------------------------------ #
    def _on_loading_changed(self, is_loading: bool):
        # جلوگیری از دابل-کلیک/ورودی هم‌زمان تا زمانی که عملیات async تمام شود
        self._new_btn.setEnabled(not is_loading)
        if is_loading and not self._first_load_done:
            self._show_skeleton()

    def _show_skeleton(self):
        """طبق بخش ۵ اسپک: "Async loading with skeleton" — فقط در اولین
        بارگذاری صفحه نمایش داده می‌شود (نه در هر refresh سریع بعدی،
        چون فلش‌زدن skeleton برای یک بازخوانی چندصدم‌ثانیه‌ای آزاردهنده
        است، نه مفید)."""
        self._clear_list()
        self._skeleton = SkeletonLoader(rows=5, row_height=48, spacing=10)
        self._list_layout.addWidget(self._skeleton)

    def _on_stats_changed(self, stats: dict):
        self._sc_total.set_value(str(stats.get("total", 0)))
        self._sc_today.set_value(str(stats.get("due_today", 0)))
        self._sc_overdue.set_value(str(stats.get("overdue", 0)))
        self._sc_done.set_value(str(stats.get("done", 0)))

    def _on_tasks_changed(self, tasks: list):
        self._first_load_done = True
        self._last_tasks = tasks
        self._render_list(tasks)
        self._render_board(tasks)
        if self._view_mode == "calendar":
            self._render_calendar()

    def _on_subtasks_changed(self, subtasks_map: dict):
        """طبق بخش ۴ اسپک: "Tasks: ... subtasks" — بعد از رسیدن async
        زیرتسک‌ها، لیست را دوباره (این‌بار با تودرتو) رندر می‌کند."""
        self._subtasks_map = subtasks_map
        if getattr(self, "_last_tasks", None) is not None:
            self._render_list(self._last_tasks)

    def _render_list(self, tasks: list):
        self._clear_list()
        if not tasks:
            empty = EmptyState("check", "تسکی پیدا نشد",
                               "برای شروع یک تسک جدید اضافه کن",
                               "+ تسک جدید")
            empty.action_clicked.connect(self._open_new_dialog)
            self._list_layout.addWidget(empty)
            return
        for t in tasks:
            item = TaskItem(t)
            item.completed.connect(self._vm.toggle_complete)
            item.edited.connect(self._edit_task)
            item.deleted.connect(self._delete_task)
            item.add_subtask_requested.connect(self._add_subtask)
            item.history_requested.connect(self._open_history)
            self._list_layout.addWidget(item)
            for sub in self._subtasks_map.get(t.id, []):
                sub_item = TaskItem(sub, indent=True)
                sub_item.completed.connect(self._vm.toggle_complete)
                sub_item.edited.connect(self._edit_task)
                sub_item.deleted.connect(self._delete_task)
                sub_item.history_requested.connect(self._open_history)
                self._list_layout.addWidget(sub_item)

    def _render_board(self, tasks: list):
        """طبق بخش ۴ اسپک — نمای بورد را با همان داده‌ی نمای لیست
        هم‌زمان به‌روز نگه می‌دارد (هر دو نما از یک منبع داده)."""
        for column in self._board_columns.values():
            column.clear()
        for t in tasks:
            column = self._board_columns.get(t.status.value)
            if not column:
                continue
            item = QListWidgetItem(t.title)
            item.setData(Qt.ItemDataRole.UserRole, t.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
            column.addItem(item)

    def _on_view_mode_changed(self, mode: str):
        self._view_mode = mode
        self._scroll.setVisible(mode == "list")
        self._board_widget.setVisible(mode == "board")
        self._calendar_widget.setVisible(mode == "calendar")
        if mode == "calendar":
            self._render_calendar()

    def _cal_prev_month(self):
        self._cal_month -= 1
        if self._cal_month < 1:
            self._cal_month = 12
            self._cal_year -= 1
        self._render_calendar()

    def _cal_next_month(self):
        self._cal_month += 1
        if self._cal_month > 12:
            self._cal_month = 1
            self._cal_year += 1
        self._render_calendar()

    def _render_calendar(self):
        """طبق بخش ۴ اسپک: "Tasks: ... calendar views" — از همان
        self._last_tasks (نمای لیست) استفاده می‌کند، بدون کوئری جدا."""
        c = colors()
        self._cal_month_lbl.setText(f"{config.MONTHS_FA[self._cal_month-1]} {self._cal_year}")

        while self._cal_grid.count():
            item = self._cal_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, wd in enumerate(config.WEEKDAY_FA):
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-size:11px;color:{c.text_secondary};font-weight:600;background:transparent;padding:4px;")
            self._cal_grid.addWidget(lbl, 0, i)

        tasks_by_date = {}
        for t in (self._last_tasks or []):
            if t.due_date:
                tasks_by_date.setdefault(t.due_date[:10], []).append(t)

        try:
            first_of_month_g = jalali_to_gregorian(self._cal_year, self._cal_month, 1)
        except Exception:
            return
        start_weekday = (first_of_month_g.weekday() + 2) % 7  # شنبه=۰

        days = 31 if self._cal_month <= 6 else (30 if self._cal_month <= 11 else 29)
        today_jy, today_jm, today_jd = today_jalali()

        row, col = 1, start_weekday
        for day in range(1, days + 1):
            try:
                g_date = jalali_to_gregorian(self._cal_year, self._cal_month, day)
            except Exception:
                break
            cell = QFrame(); cell.setProperty("class", "card")
            cell.setMinimumHeight(64)
            is_today = (self._cal_year, self._cal_month, day) == (today_jy, today_jm, today_jd)
            if is_today:
                cell.setStyleSheet(f"QFrame{{background:{c.primary}22;border:1px solid {c.primary};border-radius:8px;}}")
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(6, 4, 6, 4)
            cl.setSpacing(2)
            day_lbl = QLabel(str(day))
            day_lbl.setStyleSheet(
                f"font-size:12px;font-weight:{'700' if is_today else '500'};"
                f"color:{c.primary if is_today else c.text_primary};background:transparent;")
            cl.addWidget(day_lbl)

            day_tasks = tasks_by_date.get(g_date.isoformat(), [])
            for t in day_tasks[:3]:
                t_lbl = QLabel(("" if t.status.value == "done" else "• ") + t.title[:14])
                t_lbl.setStyleSheet(f"font-size:9px;color:{c.text_secondary};background:transparent;")
                cl.addWidget(t_lbl)
            if len(day_tasks) > 3:
                more_lbl = QLabel(f"+{len(day_tasks)-3}")
                more_lbl.setStyleSheet(f"font-size:9px;color:{c.text_secondary};background:transparent;")
                cl.addWidget(more_lbl)

            self._cal_grid.addWidget(cell, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _on_task_dropped_on_column(self, task_id: int):
        column = self.sender()
        if isinstance(column, _BoardColumn):
            self._vm.update(task_id, status=column.status_value)

    def _clear_list(self):
        if getattr(self, "_skeleton", None) is not None:
            self._skeleton.stop()
            self._skeleton = None
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    # ------------------------------------------------------------------ #
    # دیالوگ‌ها — فقط داده جمع می‌کنند و به ViewModel می‌سپارند
    # ------------------------------------------------------------------ #
    def _on_categories_changed(self, categories: list):
        self._categories_cache = categories

    def _open_new_dialog(self):
        dlg = TaskFormDialog(self, categories=self._categories_cache)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._vm.create(**dlg.get_data())

    def _on_quick_add(self):
        title = self._quick_add_input.text().strip()
        if not title:
            return
        self._vm.create(title=title)
        self._quick_add_input.clear()

    def _add_subtask(self, parent_id: int):
        dlg = TaskFormDialog(self, categories=self._categories_cache)
        dlg.setWindowTitle("زیرتسک جدید")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            title = data.pop("title")
            self._vm.create_subtask(parent_id, title, **data)

    def _open_history(self, task_id: int):
        self._vm.load_history(task_id)

    def _on_history_loaded(self, entries: list):
        dlg = HistoryDialog(self, "تاریخچه‌ی تسک", entries)
        dlg.restore_requested.connect(self._vm.restore_from_history)
        dlg.exec()

    def _edit_task(self, task_id: int):
        def _on_loaded(task):
            if not task:
                return
            dlg = TaskFormDialog(self, task, categories=self._categories_cache)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self._vm.update(task_id, **dlg.get_data())
        self._vm.fetch_task_for_edit(task_id, _on_loaded)

    def _delete_task(self, task_id: int):
        if confirm(self, "حذف تسک", "آیا از حذف این تسک مطمئنی؟", "حذف", danger=True):
            self._vm.remove(task_id)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)

    def _on_undo_performed(self, description: str):
        """اعلان واقعی Toast برای بازگردانی موفق — فقط وقتی undo از طریق
        میان‌بر Ctrl+Z اجرا شده باشد (نه از دکمه‌ی خودِ Toast، چون در آن
        حالت محوشدن خودِ Toast قبلاً بازخورد کافی داده است)."""
        if self._suppress_next_undo_toast:
            self._suppress_next_undo_toast = False
            return
        show_toast(self, f"بازگردانده شد: {description}")

    def _on_undo_available_changed(self, available: bool):
        """درست بعد از یک اقدام مخرب (مثل حذف تسک)، یک Toast اقدام‌پذیر
        با دکمه‌ی «واگرد» نشان می‌دهد — این همان «Toast with undo action»ی
        است که بخش ۹ اسپک می‌خواست."""
        if not available:
            return
        description = self._vm.peek_undo_description()
        if description:
            def _on_action():
                self._suppress_next_undo_toast = True
                self._vm.undo_last()
            show_toast(self, description, action_text="واگرد", on_action=_on_action)
