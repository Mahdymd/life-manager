"""
ui/viewmodels/finance_viewmodel.py

ViewModel صفحه‌ی مالی. الگو از task_list_viewmodel.py.

نکته: دسته‌بندی‌ها (categories) به‌صورت جداگانه و فقط یک‌بار (در
setup_ui صفحه) بارگذاری و کش می‌شوند، چون به‌ندرت در طول عمر این صفحه
تغییر می‌کنند و دیالوگ تراکنش برای باز شدن فوری به آن‌ها نیاز دارد.
"""

from __future__ import annotations
from datetime import date
from typing import Dict, List
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.domain.models import Transaction, Budget
from core.services.finance_service import (
    get_summary,
    get_transactions,
    get_budgets,
    get_expense_by_category,
    add_transaction,
    update_transaction,
    delete_transaction,
)


def _fetch_categories() -> List:
    """این تابع در worker thread اجرا می‌شود؛ import محلی برای جلوگیری
    از وابستگی چرخه‌ای در سطح ماژول."""
    from core.repositories.tag_repository import TagRepository
    return TagRepository().get_category_all("finance")


class FinanceViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی مالی.

    Signals:
        summary_changed(dict)
        transactions_changed(list[Transaction])
        budgets_changed(list[Budget])
        categories_changed(list)
    """

    summary_changed = Signal(dict)
    transactions_changed = Signal(list)
    budgets_changed = Signal(list)
    categories_changed = Signal(list)
    budget_alert = Signal(str)
    category_breakdown_changed = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._month: str = date.today().isoformat()[:7]
        self._summary: Dict = {}
        self._transactions: List[Transaction] = []
        self._budgets: List[Budget] = []
        self._categories: List = []
        # از تکرار هشدار برای یک دسته‌بندی در طول یک session جلوگیری
        # می‌کند (وگرنه با هر refresh بعد از هر تراکنش دوباره Toast می‌آمد)
        self._warned_categories: set = set()

    @property
    def categories(self) -> List:
        return self._categories

    def load(self) -> None:
        """آمار ماه، تراکنش‌ها و بودجه‌ها را (همه async) بازخوانی می‌کند."""
        month = self._month
        self.run_async(get_summary, self._on_summary_loaded, month)
        self.run_async(get_transactions, self._on_transactions_loaded, month=month)
        self.run_async(get_budgets, self._on_budgets_loaded)
        self.run_async(get_expense_by_category, self._on_category_breakdown_loaded, month)

    def load_categories(self) -> None:
        self.run_async(_fetch_categories, self._on_categories_loaded)

    def _on_summary_loaded(self, summary: Dict) -> None:
        self._summary = summary
        self.summary_changed.emit(summary)

    def _on_transactions_loaded(self, txs: List[Transaction]) -> None:
        self._transactions = txs
        self.transactions_changed.emit(txs)

    def _on_budgets_loaded(self, budgets: List[Budget]) -> None:
        self._budgets = budgets
        self.budgets_changed.emit(budgets)
        self._check_budget_alerts(budgets)

    def _check_budget_alerts(self, budgets: List[Budget]) -> None:
        for b in budgets:
            if not b.monthly_limit:
                continue
            pct = (b.spent / b.monthly_limit) * 100
            if pct >= b.alert_at_pct and b.category_id not in self._warned_categories:
                self._warned_categories.add(b.category_id)
                name = b.category_name or "این دسته‌بندی"
                if pct >= 100:
                    msg = f"بودجه‌ی «{name}» تمام شد ({int(pct)}٪ مصرف‌شده)"
                else:
                    msg = f"نزدیک به سقف بودجه‌ی «{name}» ({int(pct)}٪ مصرف‌شده)"
                self.budget_alert.emit(msg)

    def _on_categories_loaded(self, categories: List) -> None:
        self._categories = categories
        self.categories_changed.emit(categories)

    def _on_category_breakdown_loaded(self, breakdown: List) -> None:
        self.category_breakdown_changed.emit(breakdown)

    def add_transaction(self, **data) -> None:
        self.run_async(add_transaction, lambda _r: self.load(), **data)

    def update_transaction(self, id_: int, **data) -> None:
        self.run_async(update_transaction, lambda _r: self.load(), id_, **data)

    def remove_transaction(self, id_: int) -> None:
        self.run_async(delete_transaction, lambda _r: self.load(), id_)
