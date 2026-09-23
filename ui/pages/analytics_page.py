"""ui/pages/analytics_page.py — Analytics و گزارش‌های جامع."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QComboBox, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from typing import Optional
from ui.pages.base_page import BasePage
from ui.style.theme_manager import colors
from ui.viewmodels.analytics_viewmodel import AnalyticsViewModel
from utils.number_utils import format_currency
import config


class SimpleBarChart(QFrame):
    """نمودار میله‌ای ساده بدون dependency خارجی."""

    def __init__(self, data: list, labels: list, color: Optional[str] = None,
                 title: str = "", y_suffix: str = "", parent=None):
        super().__init__(parent)
        self._data = data
        self._labels = labels
        self._color = QColor(color or colors().primary)
        self._title = title
        self._y_suffix = y_suffix
        self.setMinimumHeight(180)
        self.setProperty("class", "card")

    def update_data(self, data: list, labels: list):
        self._data = data
        self._labels = labels
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 48, 16, 32, 36

        chart_w = W - pad_l - pad_r
        chart_h = H - pad_t - pad_b

        max_val = max(self._data) if max(self._data) > 0 else 1
        bar_w = max(4, chart_w // max(len(self._data), 1) - 6)

        # Title
        if self._title:
            painter.setPen(QColor(colors().text_secondary))
            f = QFont("Vazirmatn", 10)
            painter.setFont(f)
            painter.drawText(pad_l, 18, self._title)

        # Bars
        for i, val in enumerate(self._data):
            bar_h = int((val / max_val) * chart_h)
            x = pad_l + i * (chart_w // len(self._data)) + (chart_w // len(self._data) - bar_w) // 2
            y = pad_t + chart_h - bar_h

            # Bar
            c = QColor(self._color)
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 3, 3)

            # Value label on top
            if val > 0:
                painter.setPen(QColor(colors().text_primary))
                f2 = QFont("Vazirmatn", 8)
                painter.setFont(f2)
                val_str = str(int(val))
                painter.drawText(x, y - 4, bar_w, 16, Qt.AlignmentFlag.AlignCenter, val_str)

            # X label
            if i < len(self._labels):
                painter.setPen(QColor(colors().text_secondary))
                f3 = QFont("Vazirmatn", 8)
                painter.setFont(f3)
                painter.drawText(x - 10, pad_t + chart_h + 6, bar_w + 20, 24,
                                 Qt.AlignmentFlag.AlignCenter, str(self._labels[i]))

        painter.end()


class SimpleLineChart(QFrame):
    """نمودار خطی ساده."""

    def __init__(self, datasets: list, color: Optional[str] = None,
                 title: str = "", parent=None):
        super().__init__(parent)
        # datasets: list of (label, values_list, color)
        self._datasets = datasets
        self._title = title
        self.setMinimumHeight(160)
        self.setProperty("class", "card")

    def update_data(self, datasets):
        self._datasets = datasets
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._datasets:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 12, 12, 28, 12
        chart_w = W - pad_l - pad_r
        chart_h = H - pad_t - pad_b

        all_vals = []
        for _, vals, _ in self._datasets:
            all_vals.extend(vals)
        if not all_vals:
            painter.end()
            return
        max_v = max(all_vals) if max(all_vals) > 0 else 1
        min_v = min(all_vals)

        if self._title:
            painter.setPen(QColor(colors().text_secondary))
            painter.setFont(QFont("Vazirmatn", 9))
            painter.drawText(pad_l, 18, self._title)

        for label, vals, color in self._datasets:
            if len(vals) < 2:
                continue
            pts = []
            step = chart_w / (len(vals) - 1) if len(vals) > 1 else chart_w
            for i, v in enumerate(vals):
                x = pad_l + int(i * step)
                y = pad_t + chart_h - int(((v - min_v) / (max_v - min_v + 0.0001)) * chart_h)
                pts.append((x, y))

            # Line
            pen = QPen(QColor(color), 2)
            painter.setPen(pen)
            for i in range(len(pts) - 1):
                painter.drawLine(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])

            # Dots
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.PenStyle.NoPen)
            for x, y in pts:
                painter.drawEllipse(x - 3, y - 3, 6, 6)

        painter.end()


class AnalyticsPage(BasePage):
    """View خالص — بدون import مستقیم از core.services/core.repositories/
    core.database؛ همه چیز از طریق self._vm (AnalyticsViewModel)."""

    def setup_ui(self):
        self._vm = AnalyticsViewModel(self)
        self._vm.weekly_summary_loaded.connect(self._on_weekly_summary_loaded)
        self._vm.task_trend_loaded.connect(self._on_task_trend_loaded)
        self._vm.finance_trend_loaded.connect(self._on_finance_trend_loaded)
        self._vm.habit_stats_loaded.connect(self._on_habit_stats_loaded)
        self._vm.health_trend_loaded.connect(self._on_health_trend_loaded)
        self._vm.mood_trend_loaded.connect(self._on_mood_trend_loaded)
        self._vm.goal_progress_loaded.connect(self._on_goal_progress_loaded)
        self._vm.insights_loaded.connect(self._on_insights_loaded)
        self._vm.error_occurred.connect(self._show_error)

        self.set_header("آنالیتیکس", "گزارش جامع عملکرد زندگی")

        refresh_btn = self.add_header_action("بروزرسانی")
        from ui.style.icons import icon as _icon
        refresh_btn.setIcon(_icon("refresh", 14, colors().primary_text))
        refresh_btn.clicked.connect(self.refresh)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_inner = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_inner)
        self._scroll_layout.setSpacing(20)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._scroll_inner)
        self._content_layout.addWidget(scroll)

        self._build_sections()
        self.refresh()

    def _build_sections(self):
        # ── Insights (هیوریستیک) ──────────────────────
        self._insights_container = QWidget()
        self._insights_layout = QVBoxLayout(self._insights_container)
        self._insights_layout.setContentsMargins(0, 0, 0, 0)
        self._insights_layout.setSpacing(8)
        self._scroll_layout.addWidget(self._insights_container)

        # ── Weekly summary cards ──────────────────────
        lbl = QLabel("خلاصه این هفته")
        lbl.setStyleSheet("font-size:16px;font-weight:700;background:transparent;")
        self._scroll_layout.addWidget(lbl)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        c = colors()
        self._wcard_tasks    = self._mini_card("تسک انجام‌شده", "—", c.success)
        self._wcard_habits   = self._mini_card("نرخ عادت‌ها", "—", c.warning)
        self._wcard_focus    = self._mini_card("دقیقه تمرکز", "—", c.primary)
        self._wcard_balance  = self._mini_card("مانده ماه", "—", c.info)
        for c in [self._wcard_tasks, self._wcard_habits,
                  self._wcard_focus, self._wcard_balance]:
            cards_row.addWidget(c)
        self._scroll_layout.addLayout(cards_row)

        # ── Task trend ───────────────────────────────
        sep1 = QLabel("روند تسک‌ها (۶ ماه اخیر)")
        sep1.setStyleSheet("font-size:15px;font-weight:600;background:transparent;margin-top:8px;")
        self._scroll_layout.addWidget(sep1)
        self._task_chart = SimpleBarChart([], [], colors().primary, "تسک‌های انجام‌شده")
        self._scroll_layout.addWidget(self._task_chart)

        # ── Finance trend ────────────────────────────
        sep2 = QLabel("روند مالی (۶ ماه اخیر)")
        sep2.setStyleSheet("font-size:15px;font-weight:600;background:transparent;margin-top:8px;")
        self._scroll_layout.addWidget(sep2)
        self._finance_chart = SimpleLineChart([], title="درآمد vs هزینه")
        self._scroll_layout.addWidget(self._finance_chart)

        # ── Habit heatmap (simple list) ──────────────
        sep3 = QLabel("بهترین عادت‌ها (۳۰ روز اخیر)")
        sep3.setStyleSheet("font-size:15px;font-weight:600;background:transparent;margin-top:8px;")
        self._scroll_layout.addWidget(sep3)
        self._habit_frame = QFrame()
        self._habit_frame.setProperty("class", "card")
        self._habit_layout = QVBoxLayout(self._habit_frame)
        self._habit_layout.setContentsMargins(16, 12, 16, 12)
        self._habit_layout.setSpacing(8)
        self._scroll_layout.addWidget(self._habit_frame)

        # ── Health trend ─────────────────────────────
        sep4 = QLabel("روند وزن")
        sep4.setStyleSheet("font-size:15px;font-weight:600;background:transparent;margin-top:8px;")
        self._scroll_layout.addWidget(sep4)
        self._health_chart = SimpleLineChart([], title="وزن (کیلوگرم)")
        self._scroll_layout.addWidget(self._health_chart)

        # ── Mood chart ───────────────────────────────
        sep5 = QLabel("روند حال (۳۰ روز اخیر)")
        sep5.setStyleSheet("font-size:15px;font-weight:600;background:transparent;margin-top:8px;")
        self._scroll_layout.addWidget(sep5)
        self._mood_chart = SimpleBarChart([], [], colors().warning, "حال روزانه (۱-۵)")
        self._scroll_layout.addWidget(self._mood_chart)

        # ── Goal progress ────────────────────────────
        sep6 = QLabel("پیشرفت اهداف فعال")
        sep6.setStyleSheet("font-size:15px;font-weight:600;background:transparent;margin-top:8px;")
        self._scroll_layout.addWidget(sep6)
        self._goals_frame = QFrame()
        self._goals_frame.setProperty("class", "card")
        self._goals_layout = QVBoxLayout(self._goals_frame)
        self._goals_layout.setContentsMargins(16, 12, 16, 12)
        self._goals_layout.setSpacing(8)
        self._scroll_layout.addWidget(self._goals_frame)

        self._scroll_layout.addStretch()

    def _mini_card(self, label: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        card.setMinimumHeight(90)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(
            f"font-size:22px;font-weight:700;color:{color};background:transparent;")
        l_lbl = QLabel(label)
        l_lbl.setStyleSheet(f"font-size:11px;color:{colors().text_secondary};background:transparent;")
        cl.addWidget(v_lbl)
        cl.addWidget(l_lbl)
        card._value_lbl = v_lbl
        return card

    def refresh(self):
        self._vm.load()

    def _on_weekly_summary_loaded(self, data: dict):
        self._wcard_tasks._value_lbl.setText(str(data.get("tasks_done", 0)))

        habit_pct = data.get("habit_pct")
        self._wcard_habits._value_lbl.setText(f"{habit_pct}%" if habit_pct is not None else "—")

        self._wcard_focus._value_lbl.setText(str(data.get("focus_min", 0)))

        bal = data.get("balance", 0)
        self._wcard_balance._value_lbl.setText(format_currency(bal))
        color = colors().success if bal >= 0 else colors().danger
        self._wcard_balance._value_lbl.setStyleSheet(
            f"font-size:20px;font-weight:700;color:{color};background:transparent;")

    def _on_task_trend_loaded(self, result):
        if result:
            vals, labels = result
            self._task_chart.update_data(vals, labels)

    def _on_finance_trend_loaded(self, result):
        if result:
            labels, incomes, expenses = result
            self._finance_chart.update_data([
                ("درآمد", incomes, colors().success),
                ("هزینه", expenses, colors().danger),
            ])

    def _on_habit_stats_loaded(self, stats: list):
        while self._habit_layout.count():
            item = self._habit_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for entry in stats:
            habit = entry["habit"]
            rate = entry["rate"]
            streak = entry["streak"]

            row = QHBoxLayout()
            icon = QLabel(habit.icon)
            icon.setStyleSheet("font-size:16px;background:transparent;")
            name = QLabel(habit.name)
            name.setStyleSheet("font-size:13px;font-weight:500;background:transparent;")
            name.setMinimumWidth(160)

            from PySide6.QtWidgets import QProgressBar
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(rate)
            pb.setFixedHeight(6)
            pb.setTextVisible(False)
            c = habit.color
            pb.setStyleSheet(
                f"QProgressBar{{background:{colors().border};border:none;border-radius:3px;}}"
                f"QProgressBar::chunk{{background:{c};border-radius:3px;}}")

            rate_lbl = QLabel(f"{rate}%")
            rate_lbl.setStyleSheet(f"font-size:11px;color:{c};font-weight:600;background:transparent;")
            rate_lbl.setFixedWidth(36)
            streak_lbl = QLabel(f"{streak}")
            streak_lbl.setStyleSheet(f"font-size:11px;color:{colors().warning};background:transparent;")
            streak_lbl.setFixedWidth(40)

            row.addWidget(icon)
            row.addWidget(name)
            row.addWidget(pb, 1)
            row.addWidget(rate_lbl)
            row.addWidget(streak_lbl)
            self._habit_layout.addLayout(row)

        if not stats:
            no_data = QLabel("هیچ عادتی ثبت نشده است.")
            no_data.setStyleSheet(f"color:{colors().text_secondary};background:transparent;")
            self._habit_layout.addWidget(no_data)

    def _on_health_trend_loaded(self, result):
        if result:
            vals, labels = result
            self._health_chart.update_data([("وزن", vals, colors().primary)])

    def _on_mood_trend_loaded(self, result):
        if result:
            vals, labels = result
            self._mood_chart.update_data(vals, labels)

    def _on_goal_progress_loaded(self, goals: list):
        while self._goals_layout.count():
            item = self._goals_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not goals:
            lbl = QLabel("هیچ هدف فعالی وجود ندارد.")
            lbl.setStyleSheet(f"color:{colors().text_secondary};background:transparent;")
            self._goals_layout.addWidget(lbl)
            return

        for goal in goals:
            row = QHBoxLayout()
            horizon_color = horizon_color(goal.horizon.value)
            badge = QLabel(config.HORIZON_LABELS.get(goal.horizon.value, ""))
            badge.setStyleSheet(
                f"background:{horizon_color}22;color:{horizon_color};"
                f"border-radius:6px;padding:1px 6px;font-size:10px;font-weight:600;")
            badge.setFixedWidth(60)

            name = QLabel(goal.title)
            name.setStyleSheet("font-size:13px;font-weight:500;background:transparent;")
            name.setMinimumWidth(180)

            from PySide6.QtWidgets import QProgressBar
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(int(goal.computed_progress))
            pb.setFixedHeight(6)
            pb.setTextVisible(False)
            pb.setStyleSheet(
                f"QProgressBar{{background:{colors().border};border:none;border-radius:3px;}}"
                f"QProgressBar::chunk{{background:{horizon_color};border-radius:3px;}}")

            pct_lbl = QLabel(f"{int(goal.computed_progress)}%")
            pct_lbl.setStyleSheet(
                f"font-size:11px;color:{horizon_color};font-weight:600;background:transparent;")
            pct_lbl.setFixedWidth(36)

            row.addWidget(badge)
            row.addWidget(name)
            row.addWidget(pb, 1)
            row.addWidget(pct_lbl)
            self._goals_layout.addLayout(row)

    def _on_insights_loaded(self, insights: list):
        """طبق بخش ۶ اسپک: "Analytics Insights: heuristic‑driven cards"."""
        while self._insights_layout.count():
            item = self._insights_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not insights:
            return  # اگر داده کافی نباشد، این بخش کاملاً پنهان می‌ماند

        c = colors()
        from ui.style.icons import icon as _icon
        for item in insights:
            card = QFrame()
            card.setProperty("class", "card")
            card.setStyleSheet(f"QFrame[class=\"card\"] {{ border-right: 3px solid {c.primary}; }}")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.setSpacing(8)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(_icon(item.get("icon", "info"), 16, c.primary).pixmap(16, 16))
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
            cl.addWidget(icon_lbl)
            lbl = QLabel(item.get("text", ""))
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size:13px;background:transparent;")
            cl.addWidget(lbl, 1)
            self._insights_layout.addWidget(card)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
