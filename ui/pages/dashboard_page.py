"""ui/pages/dashboard_page.py — داشبورد اصلی برنامه."""

from PySide6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QFrame, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from ui.pages.base_page import BasePage
from ui.components.stat_card import StatCard, MiniStatCard
from ui.style.theme_manager import colors
from ui.viewmodels.dashboard_viewmodel import DashboardViewModel
from utils.date_utils import format_jalali, today_jalali, today_iso, weekday_name_fa
from utils.number_utils import format_currency
import config

_DEFAULT_WIDGET_ORDER = ["stats", "today", "quick_actions"]


class _DashboardWidgetContainer(QFrame):
    """پوششی دور هر «ویجت» داشبورد که امکان جابه‌جایی (بالا/پایین) و
    ذخیره‌ی چیدمان را می‌دهد.

    طبق بخش ۴ اسپک: "Dashboard: ... widget-based layout (reorderable,
    persisted)". به‌جای drag-and-drop خام بین ویجت‌های دلخواه در یک
    QVBoxLayout (که در Qt به‌طور بومی و پایدار پشتیبانی نمی‌شود)، از
    دکمه‌های صریح ▲/▼ استفاده شده — قابل‌اعتمادتر و برای کاربر هم روشن‌تر
    از اینکه چه چیزی reorder می‌شود.

    Signals (از طریق callback، نه Signal رسمی Qt، چون این کلاس همیشه
    مستقیم توسط DashboardPage ساخته و مدیریت می‌شود):
    """

    def __init__(self, widget_id: str, title: str, content: QWidget,
                 on_move_up, on_move_down, icon_name: str = None, parent=None):
        super().__init__(parent)
        self.widget_id = widget_id
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(6)
        if icon_name:
            from ui.style.icons import icon as _icon
            icon_lbl = QLabel()
            icon_lbl.setPixmap(_icon(icon_name, 15, colors().text_secondary).pixmap(15, 15))
            header.addWidget(icon_lbl)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent;")
        header.addWidget(title_lbl)
        header.addStretch()

        up_btn = QPushButton("▲")
        up_btn.setProperty("class", "icon")
        up_btn.setToolTip("جابه‌جایی به بالا")
        up_btn.setFixedSize(24, 24)
        up_btn.clicked.connect(lambda: on_move_up(widget_id))
        down_btn = QPushButton("▼")
        down_btn.setProperty("class", "icon")
        down_btn.setToolTip("جابه‌جایی به پایین")
        down_btn.setFixedSize(24, 24)
        down_btn.clicked.connect(lambda: on_move_down(widget_id))
        header.addWidget(up_btn)
        header.addWidget(down_btn)
        layout.addLayout(header)

        layout.addWidget(content)


class DashboardPage(BasePage):
    """View خالص — بدون import مستقیم از core.services؛ همه چیز از طریق
    self._vm (DashboardViewModel)."""

    def setup_ui(self):
        self._vm = DashboardViewModel(self)
        self._vm.stats_changed.connect(self._on_stats_changed)
        self._vm.today_tasks_changed.connect(self._on_today_tasks_changed)
        self._vm.habits_changed.connect(self._on_habits_changed)
        self._vm.error_occurred.connect(self._show_error)

        self.set_header("داشبورد", "")
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._inner = QWidget()
        self._inner_layout = QVBoxLayout(self._inner)
        self._inner_layout.setSpacing(24)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll.setWidget(self._inner)
        self._content_layout.addWidget(self._scroll)

        self._build_greeting()

        # طبق بخش ۴ اسپک: "widget-based layout (reorderable, persisted)"
        # سه بخش قابل‌جابه‌جایی؛ خوش‌آمدگویی همیشه بالای صفحه ثابت می‌ماند
        # (یک هدر است، نه یک «ویجت»).
        self._widgets = {
            "stats": self._build_stat_cards(),
            "today": self._build_today_section(),
            "quick_actions": self._build_quick_actions(),
        }
        self._widget_titles = {
            "stats": (None, "آمار سریع"),
            "today": ("note", "امروز"),
            "quick_actions": (None, "دسترسی سریع"),
        }
        self._widget_order = self._load_widget_order()
        self._rebuild_layout()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(60000)
        self.refresh()

    # ────────────────────────────────────────────────────────────
    # چیدمان قابل‌جابه‌جایی و پایدار (از طریق SettingsManager)
    # ────────────────────────────────────────────────────────────
    def _load_widget_order(self) -> list:
        from core.services.settings_manager import get_settings_manager
        saved = get_settings_manager().dashboard_widget_order()
        if saved and isinstance(saved, list):
            # اعتبارسنجی: فقط شناسه‌های شناخته‌شده و کامل را قبول کن
            # (وگرنه اگر بعداً یک ویجت جدید اضافه شود، از دید کاربر گم می‌شود)
            valid = [w for w in saved if w in _DEFAULT_WIDGET_ORDER]
            if set(valid) == set(_DEFAULT_WIDGET_ORDER):
                return valid
        return list(_DEFAULT_WIDGET_ORDER)

    def _save_widget_order(self) -> None:
        from core.services.settings_manager import get_settings_manager
        get_settings_manager().set_dashboard_widget_order(self._widget_order)

    def _rebuild_layout(self) -> None:
        # حذف همه‌چیز بعد از خوش‌آمدگویی (ایندکس ۰) — از انتها به ابتدا
        # تا هنگام takeAt ایندکس‌ها به‌هم نریزد
        while self._inner_layout.count() > 1:
            item = self._inner_layout.takeAt(1)
            if item.widget():
                item.widget().setParent(None)

        for widget_id in self._widget_order:
            content = self._widgets.get(widget_id)
            if content is None:
                continue
            icon_name, title_text = self._widget_titles[widget_id]
            container = _DashboardWidgetContainer(
                widget_id, title_text, content,
                self._move_widget_up, self._move_widget_down, icon_name,
            )
            self._inner_layout.insertWidget(self._inner_layout.count(), container)
        self._inner_layout.addStretch()

    def _move_widget_up(self, widget_id: str) -> None:
        idx = self._widget_order.index(widget_id)
        if idx > 0:
            self._widget_order[idx - 1], self._widget_order[idx] = \
                self._widget_order[idx], self._widget_order[idx - 1]
            self._save_widget_order()
            self._rebuild_layout()

    def _move_widget_down(self, widget_id: str) -> None:
        idx = self._widget_order.index(widget_id)
        if idx < len(self._widget_order) - 1:
            self._widget_order[idx + 1], self._widget_order[idx] = \
                self._widget_order[idx], self._widget_order[idx + 1]
            self._save_widget_order()
            self._rebuild_layout()

    def _build_greeting(self):
        jy, jm, jd = today_jalali()
        date_str = format_jalali(fmt="named")
        wd = weekday_name_fa()

        frame = QFrame()
        frame.setProperty("class", "card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 20)

        left = QVBoxLayout()
        greeting_row = QHBoxLayout()
        greeting_row.setSpacing(8)
        self._greeting_lbl = QLabel("سلام!")
        self._greeting_lbl.setStyleSheet(
            "font-size: 22px; font-weight: 700; background: transparent;")
        greeting_row.addWidget(self._greeting_lbl)
        from ui.style.icons import icon as _icon
        greeting_icon = QLabel()
        greeting_icon.setPixmap(_icon("smile", 22, colors().primary).pixmap(22, 22))
        greeting_row.addWidget(greeting_icon)
        greeting_row.addStretch()
        self._date_lbl = QLabel(f"{wd}، {date_str}")
        self._date_lbl.setStyleSheet(
            f"font-size: 14px; color: {colors().text_secondary}; background: transparent;")
        left.addLayout(greeting_row)
        left.addWidget(self._date_lbl)
        layout.addLayout(left)
        layout.addStretch()

        self._inner_layout.addWidget(frame)

    def _build_stat_cards(self):
        wrapper = QWidget()
        grid = QGridLayout(wrapper)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(16)

        c = colors()
        self._card_tasks   = StatCard("check",  "تسک‌های امروز",  "–", "", c.primary)
        self._card_habits  = StatCard("flame",  "عادت‌های امروز", "–", "", c.warning)
        self._card_finance = StatCard("money",  "تراز ماه",        "–", "", c.success)
        self._card_focus   = StatCard("focus",  "پومودورو امروز",  "–", "", c.danger)

        grid.addWidget(self._card_tasks,   0, 0)
        grid.addWidget(self._card_habits,  0, 1)
        grid.addWidget(self._card_finance, 0, 2)
        grid.addWidget(self._card_focus,   0, 3)
        return wrapper

    def _build_today_section(self):
        wrapper = QWidget()
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(16)

        # تسک‌های امروز
        tasks_frame = QFrame()
        tasks_frame.setProperty("class", "card")
        tl = QVBoxLayout(tasks_frame)
        tl.setContentsMargins(20, 16, 20, 16)
        th = QHBoxLayout()
        th.setSpacing(6)
        from ui.style.icons import icon as _icon2
        tl_icon = QLabel()
        tl_icon.setPixmap(_icon2("check", 14, colors().text_secondary).pixmap(14, 14))
        th.addWidget(tl_icon)
        tl_title = QLabel("تسک‌های امروز")
        tl_title.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent;")
        th.addWidget(tl_title); th.addStretch()
        tl.addLayout(th)
        self._tasks_list_layout = QVBoxLayout()
        self._tasks_list_layout.setSpacing(6)
        tl.addLayout(self._tasks_list_layout)
        row.addWidget(tasks_frame, 3)

        # عادت‌های امروز
        habits_frame = QFrame()
        habits_frame.setProperty("class", "card")
        hl2 = QVBoxLayout(habits_frame)
        hl2.setContentsMargins(20, 16, 20, 16)
        hh = QHBoxLayout()
        hh.setSpacing(6)
        from ui.style.icons import icon as _icon5
        hh_icon = QLabel()
        hh_icon.setPixmap(_icon5("flame", 14, colors().warning).pixmap(14, 14))
        hh.addWidget(hh_icon)
        hl_title = QLabel("عادت‌های امروز")
        hl_title.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent;")
        hh.addWidget(hl_title); hh.addStretch()
        hl2.addLayout(hh)
        self._habits_list_layout = QVBoxLayout()
        self._habits_list_layout.setSpacing(6)
        hl2.addLayout(self._habits_list_layout)
        row.addWidget(habits_frame, 2)

        return wrapper

    def _build_quick_actions(self):
        wrapper = QWidget()
        fl = QVBoxLayout(wrapper)
        fl.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.setSpacing(10)
        actions = [
            ("تسک جدید", "tasks", True), ("هدف جدید", "goals", True),
            ("تراکنش", "finance", True), ("روزانه", "journal", False),
            ("فوکوس", "focus", False),
        ]
        for label, module, create in actions:
            btn = QPushButton(label)
            btn.setProperty("class", "ghost")
            btn.setStyleSheet(btn.styleSheet() + f"border: 1px solid {colors().border}; border-radius: 8px;")
            if create:
                btn.clicked.connect(lambda _, m=module: self.request_create.emit(m))
            else:
                btn.clicked.connect(lambda _, m=module: self.request_navigate.emit(m))
            row.addWidget(btn)
        fl.addLayout(row)
        return wrapper

    def _update_time(self):
        from utils.date_utils import format_jalali
        from datetime import date
        weekdays = ["دوشنبه","سه‌شنبه","چهارشنبه","پنج‌شنبه","جمعه","شنبه","یکشنبه"]
        wd = weekdays[date.today().weekday()]
        self._date_lbl.setText(f"{wd}، {format_jalali(fmt='named')}")

    def refresh(self):
        self._vm.load()

    def _on_stats_changed(self, data: dict):
        t = data.get("tasks", {})
        h = data.get("habits", {})
        f_data = data.get("finance", {})
        foc = data.get("focus", {})
        total = t.get("due_today", 0) or 0
        done  = t.get("done", 0) or 0
        self._card_tasks.update_value(str(total), f"{done} انجام‌شده")
        self._card_habits.update_value(
            f"{h.get('done_today',0)}/{h.get('total',0)}", "امروز")
        bal = f_data.get("balance", 0) or 0
        self._card_finance.update_value(
            format_currency(bal), "درآمد - هزینه")
        pom = foc.get("today_pomodoros", 0) or 0
        self._card_focus.update_value(str(pom), "جلسه فوکوس")

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_today_tasks_changed(self, tasks: list):
        self._clear_layout(self._tasks_list_layout)
        if not tasks:
            lbl = QLabel("امروز تسکی ندارید")
            lbl.setStyleSheet(f"color: {colors().text_secondary}; font-size: 13px; background: transparent;")
            self._tasks_list_layout.addWidget(lbl)
            return
        from ui.style.icons import icon as _icon3
        for t in tasks:
            row = QHBoxLayout()
            done = t.status.value == "done"
            c = colors()
            icon = QLabel()
            if done:
                icon.setPixmap(_icon3("check", 14, c.success).pixmap(14, 14))
            else:
                icon.setText("○")
                icon.setStyleSheet(f"color: {c.text_disabled}; background: transparent;")
            icon.setFixedWidth(24)
            lbl = QLabel(t.title)
            lbl.setStyleSheet(
                f"font-size: 13px; background: transparent;"
                f"{f'text-decoration: line-through; color: {colors().text_secondary};' if done else ''}")
            priority_colors = {"urgent": c.danger, "high": c.priority_high, "medium": c.primary, "low": c.success}
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {priority_colors.get(t.priority.value, c.primary)}; background: transparent; font-size: 10px;")
            row.addWidget(icon); row.addWidget(lbl); row.addStretch(); row.addWidget(dot)
            w = QWidget(); w.setLayout(row)
            self._tasks_list_layout.addWidget(w)

    def _on_habits_changed(self, habits: list):
        self._clear_layout(self._habits_list_layout)
        if not habits:
            lbl = QLabel("عادتی تعریف نشده")
            lbl.setStyleSheet(f"color: {colors().text_secondary}; font-size: 13px; background: transparent;")
            self._habits_list_layout.addWidget(lbl)
            return
        from ui.style.icons import icon as _icon4
        for h in habits:
            row = QHBoxLayout()
            c = colors()
            icon = QLabel()
            icon.setPixmap(_icon4("check" if h.logged_today else "empty",
                                  14, c.success if h.logged_today else c.text_disabled).pixmap(14, 14))
            icon.setFixedWidth(24)
            lbl = QLabel(f"{h.icon} {h.name}")
            lbl.setStyleSheet(
                f"font-size: 13px; background: transparent;"
                f"{f'color: {colors().text_secondary};' if not h.logged_today else ''}")
            streak = QLabel(f"{h.current_streak}")
            streak.setStyleSheet(f"font-size: 11px; color: {colors().warning}; background: transparent;")
            row.addWidget(icon); row.addWidget(lbl); row.addStretch(); row.addWidget(streak)
            w = QWidget(); w.setLayout(row)
            self._habits_list_layout.addWidget(w)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
