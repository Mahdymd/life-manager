"""ui/pages/finance_page.py — صفحه مالی."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton, QLineEdit, QComboBox, QDialog,
    QFormLayout, QTabWidget, QListWidget, QListWidgetItem,
    QDoubleSpinBox, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt
from ui.pages.base_page import BasePage
from ui.components.stat_card import StatCard
from ui.components.confirm_dialog import confirm
from ui.style.theme_manager import colors
from ui.viewmodels.finance_viewmodel import FinanceViewModel
from ui.components.toast import show_toast
from ui.components.donut_chart import DonutChart
from utils.date_utils import format_jalali, parse_jalali_input, today_iso
from utils.number_utils import format_currency
import config


class TransactionFormDialog(QDialog):
    def __init__(self, parent=None, tx=None, categories=None):
        super().__init__(parent)
        self.setWindowTitle("تراکنش جدید" if not tx else "ویرایش تراکنش")
        self.setMinimumWidth(420)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self._tx = tx
        self._categories = categories or []
        self._setup_ui()
        if tx:
            self._populate(tx)

    def _setup_ui(self):
        c = colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        hdr = QLabel("" + self.windowTitle())
        hdr.setStyleSheet("font-size:17px;font-weight:700;background:transparent;")
        layout.addWidget(hdr)

        # Type selector
        type_row = QHBoxLayout()
        self._type_btns = {}
        for t, label, color in [("income","درآمد",c.success),
                                  ("expense","هزینه",c.danger),
                                  ("transfer","انتقال",c.primary)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton{{background:transparent;border:1px solid {c.border};
                border-radius:8px;padding:6px 14px;}}
                QPushButton:checked{{background:{color};color:white;border-color:{color};}}
                QPushButton:hover:!checked{{background:{c.surface_elev};}}
            """)
            btn.clicked.connect(lambda _, t_=t: self._select_type(t_))
            self._type_btns[t] = btn
            type_row.addWidget(btn)
        type_row.addStretch()
        layout.addLayout(type_row)
        self._type_btns["income"].setChecked(True)
        self._selected_type = "income"

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._amount = QDoubleSpinBox()
        self._amount.setRange(0, 999_999_999_999)
        self._amount.setDecimals(0)
        self._amount.setGroupSeparatorShown(True)
        self._amount.setSuffix(" تومان")
        self._amount.setMinimumHeight(36)
        form.addRow("مبلغ *:", self._amount)

        self._date_edit = QLineEdit()
        self._date_edit.setText(format_jalali(iso_str=today_iso()))
        form.addRow("تاریخ *:", self._date_edit)

        self._category = QComboBox()
        self._category.addItem("بدون دسته‌بندی", None)
        for cat in self._categories:
            self._category.addItem(cat["name"], cat["id"])
        form.addRow("دسته‌بندی:", self._category)

        self._note = QLineEdit()
        self._note.setPlaceholderText("توضیحات (اختیاری)")
        form.addRow("توضیحات:", self._note)

        layout.addLayout(form)

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

    def _select_type(self, t: str):
        self._selected_type = t
        for k, btn in self._type_btns.items():
            btn.setChecked(k == t)

    def _populate(self, tx):
        self._select_type(tx.type.value)
        self._amount.setValue(tx.amount)
        self._date_edit.setText(format_jalali(iso_str=tx.date))
        self._note.setText(tx.note or "")
        if tx.category_id:
            idx = self._category.findData(tx.category_id)
            if idx >= 0:
                self._category.setCurrentIndex(idx)

    def _save(self):
        if self._amount.value() <= 0:
            self._amount.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        d = parse_jalali_input(self._date_edit.text())
        return {
            "type_":       self._selected_type,
            "amount":      self._amount.value(),
            "date":        d.isoformat() if d else today_iso(),
            "category_id": self._category.currentData(),
            "note":        self._note.text().strip() or None,
        }


class FinancePage(BasePage):
    """View خالص — بدون import مستقیم از core.services/core.repositories؛
    همه چیز از طریق self._vm (FinanceViewModel)."""

    def setup_ui(self):
        self._vm = FinanceViewModel(self)
        self._vm.summary_changed.connect(self._on_summary_changed)
        self._vm.transactions_changed.connect(self._on_transactions_changed)
        self._vm.budgets_changed.connect(self._on_budgets_changed)
        self._vm.budget_alert.connect(self._on_budget_alert)
        self._vm.category_breakdown_changed.connect(self._on_category_breakdown_changed)
        self._vm.categories_changed.connect(self._on_categories_changed)
        self._vm.loading_changed.connect(self._on_loading_changed)
        self._vm.error_occurred.connect(self._show_error)
        self._categories_cache = []

        self.set_header("مالی", "مدیریت درآمد، هزینه‌ها و پس‌انداز")
        self._add_btn = self.add_header_action("+ تراکنش جدید")
        self._add_btn.clicked.connect(lambda: self._open_form())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        self._inner_layout = QVBoxLayout(inner)
        self._inner_layout.setSpacing(20)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(inner)
        self._content_layout.addWidget(scroll)

        self._build_summary_cards()
        self._build_breakdown_section()
        self._build_transactions_section()
        self._build_budgets_section()
        self._inner_layout.addStretch()
        self.refresh()
        self._vm.load_categories()

    def _build_summary_cards(self):
        row = QHBoxLayout()
        row.setSpacing(16)
        c = colors()
        self._card_income  = StatCard("trending_up",   "درآمد ماه", "—", accent_color=c.success)
        self._card_expense = StatCard("trending_down", "هزینه ماه", "—", accent_color=c.danger)
        self._card_balance = StatCard("money",         "مانده",     "—", accent_color=c.primary)
        for c in [self._card_income, self._card_expense, self._card_balance]:
            row.addWidget(c)
        self._inner_layout.addLayout(row)

    def _build_breakdown_section(self):
        lbl = QLabel("تفکیک هزینه‌ها بر اساس دسته‌بندی")
        lbl.setStyleSheet("font-size:15px;font-weight:600;background:transparent;")
        self._inner_layout.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(20)
        self._donut = DonutChart(size=160, thickness=20)
        row.addWidget(self._donut, 0, Qt.AlignmentFlag.AlignTop)

        self._legend_widget = QWidget()
        self._legend_layout = QVBoxLayout(self._legend_widget)
        self._legend_layout.setSpacing(6)
        self._legend_layout.setContentsMargins(0, 8, 0, 0)
        row.addWidget(self._legend_widget, 1)
        self._inner_layout.addLayout(row)

    def _build_transactions_section(self):
        hdr = QHBoxLayout()
        lbl = QLabel("آخرین تراکنش‌ها")
        lbl.setStyleSheet("font-size:15px;font-weight:600;background:transparent;")
        hdr.addWidget(lbl)
        hdr.addStretch()
        self._inner_layout.addLayout(hdr)

        self._tx_list = QListWidget()
        self._tx_list.setAlternatingRowColors(True)
        self._tx_list.setMinimumHeight(200)
        self._tx_list.setMaximumHeight(350)
        self._tx_list.itemDoubleClicked.connect(self._on_tx_double_click)
        self._inner_layout.addWidget(self._tx_list)

    def _build_budgets_section(self):
        lbl = QLabel("بودجه‌های ماهانه")
        lbl.setStyleSheet("font-size:15px;font-weight:600;background:transparent;")
        self._inner_layout.addWidget(lbl)
        self._budget_widget = QWidget()
        self._budget_layout = QVBoxLayout(self._budget_widget)
        self._budget_layout.setSpacing(8)
        self._budget_layout.setContentsMargins(0, 0, 0, 0)
        self._inner_layout.addWidget(self._budget_widget)

    def refresh(self):
        self._vm.load()

    def _on_loading_changed(self, is_loading: bool):
        self._add_btn.setEnabled(not is_loading)

    def _on_summary_changed(self, summary: dict):
        self._card_income.update_value(format_currency(summary.get("income", 0)))
        self._card_expense.update_value(format_currency(summary.get("expense", 0)))
        bal = summary.get("balance", 0)
        self._card_balance.update_value(
            format_currency(bal),
            subtitle="مثبت" if bal >= 0 else "منفی"
        )
        self._card_balance._value_lbl.setStyleSheet(
            f"font-size:26px;font-weight:700;background:transparent;"
            f"color:{colors().success if bal >= 0 else colors().danger};"
        )

    def _on_transactions_changed(self, txs: list):
        self._tx_list.clear()
        for tx in txs[:50]:
            color = colors().success if tx.type.value == "income" else colors().danger
            sign  = "+" if tx.type.value == "income" else "-"
            cat   = tx.category_name or "متفرقه"
            date_fa = format_jalali(iso_str=tx.date, fmt="short")
            text = f"  {date_fa}  ·  {cat}  ·  {tx.note or ''}  "
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, tx)
            self._tx_list.addItem(item)

    def _on_budgets_changed(self, budgets: list):
        while self._budget_layout.count():
            i = self._budget_layout.takeAt(0)
            if i.widget():
                i.widget().deleteLater()
        for b in budgets:
            row = QFrame()
            row.setProperty("class", "card")
            rl = QVBoxLayout(row)
            rl.setContentsMargins(14, 10, 14, 10)
            rl.setSpacing(6)
            top = QHBoxLayout()
            lbl2 = QLabel(b.category_name or "")
            lbl2.setStyleSheet("font-size:13px;font-weight:500;background:transparent;")
            pct = int((b.spent / b.monthly_limit * 100)) if b.monthly_limit else 0
            c = colors()
            color2 = c.danger if pct >= 100 else c.warning if pct >= b.alert_at_pct else c.success
            pct_lbl = QLabel(f"{format_currency(b.spent)} / {format_currency(b.monthly_limit)}")
            pct_lbl.setStyleSheet(f"font-size:12px;color:{color2};background:transparent;")
            top.addWidget(lbl2)
            top.addStretch()
            top.addWidget(pct_lbl)
            rl.addLayout(top)
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(min(pct, 100))
            pb.setFixedHeight(6)
            pb.setStyleSheet(f"QProgressBar{{background:{c.border};border:none;border-radius:3px;}}"
                             f"QProgressBar::chunk{{background:{color2};border-radius:3px;}}")
            rl.addWidget(pb)
            self._budget_layout.addWidget(row)

    def _on_categories_changed(self, categories: list):
        self._categories_cache = categories

    def _open_form(self, tx=None):
        dlg = TransactionFormDialog(self, tx, self._categories_cache)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if tx:
                self._vm.update_transaction(
                    tx.id, **{k: v for k, v in data.items() if k not in ["type_"]})
            else:
                self._vm.add_transaction(**data)

    def _on_tx_double_click(self, item: QListWidgetItem):
        tx = item.data(Qt.ItemDataRole.UserRole)
        if tx:
            self._open_form(tx)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)

    def _on_budget_alert(self, message: str):
        show_toast(self, message, duration_ms=6000, icon="warning")

    def _on_category_breakdown_changed(self, breakdown: list):
        # پالت رنگ چرخشی از توکن‌های تم (نه hex ثابت) — چون دسته‌بندی‌ها
        # پویا و تعریف‌شده توسط کاربرند و رنگ اختصاصی ندارند
        c = colors()
        palette = [c.primary, c.danger, c.warning, c.success, c.info,
                   c.priority_high, c.accent_purple]

        while self._legend_layout.count():
            item = self._legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not breakdown:
            self._donut.set_data([])
            empty_lbl = QLabel("هزینه‌ای برای این ماه ثبت نشده است.")
            empty_lbl.setStyleSheet(f"color:{c.text_secondary};font-size:12px;background:transparent;")
            self._legend_layout.addWidget(empty_lbl)
            return

        total = sum(amount for _, amount in breakdown)
        segments = [
            (name, amount, palette[i % len(palette)])
            for i, (name, amount) in enumerate(breakdown)
        ]
        self._donut.set_data(segments, center_label=format_currency(total))

        for i, (name, amount) in enumerate(breakdown):
            row = QHBoxLayout()
            row.setSpacing(8)
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{palette[i % len(palette)]};background:transparent;font-size:12px;")
            dot.setFixedWidth(16)
            name_lbl = QLabel(name or "متفرقه")
            name_lbl.setStyleSheet("font-size:12px;background:transparent;")
            pct = (amount / total * 100) if total else 0
            amount_lbl = QLabel(f"{format_currency(amount)}  ({pct:.0f}٪)")
            amount_lbl.setStyleSheet(f"font-size:11px;color:{c.text_secondary};background:transparent;")
            row.addWidget(dot)
            row.addWidget(name_lbl)
            row.addStretch()
            row.addWidget(amount_lbl)
            row_widget = QWidget()
            row_widget.setLayout(row)
            self._legend_layout.addWidget(row_widget)
