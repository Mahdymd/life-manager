"""core/services/finance_service.py"""

from typing import List, Dict, Tuple, Optional
from core.repositories.finance_repository import FinanceRepository
from core.domain.models import Transaction, Budget, SavingGoal
from utils.validator import require, require_positive

_repo = FinanceRepository()


def add_transaction(type_: str, amount: float, date: str, **kwargs) -> Transaction:
    require(type_, "نوع تراکنش")
    require_positive(amount, "مبلغ")
    require(date, "تاریخ")
    return _repo.add(type_, amount, date, **kwargs)


def update_transaction(id_: int, **kwargs) -> bool:
    return _repo.update(id_, **kwargs)


def delete_transaction(id_: int) -> bool:
    return _repo.delete(id_)


def get_transactions(**kwargs) -> List[Transaction]:
    return _repo.get_transactions(**kwargs)


def get_summary(month: str) -> Dict:
    return _repo.get_summary(month)


def get_expense_by_category(month: str) -> List[Tuple]:
    return _repo.get_expense_by_category(month)


def get_monthly_trend(months: int = 6) -> List[Dict]:
    return _repo.get_monthly_trend(months)


def upsert_budget(category_id: int, monthly_limit: float, alert_at_pct: int = 85) -> None:
    require_positive(monthly_limit, "سقف بودجه")
    _repo.upsert_budget(category_id, monthly_limit, alert_at_pct)


def get_budgets() -> List[Budget]:
    budgets = _repo.get_budgets()
    from datetime import date
    month = date.today().isoformat()[:7]
    by_cat = {r[0]: r[1] for r in _repo.get_expense_by_category(month)}
    for b in budgets:
        b.spent = by_cat.get(b.category_name, 0.0)
    return budgets


def get_saving_goals() -> List[SavingGoal]:
    return _repo.get_saving_goals()


def add_saving_goal(title: str, target_amount: float, **kwargs) -> int:
    require(title, "عنوان هدف پس‌انداز")
    require_positive(target_amount, "مبلغ هدف")
    return _repo.add_saving_goal(title, target_amount, **kwargs)


def update_saving_goal(id_: int, **kwargs) -> bool:
    return _repo.update_saving_goal(id_, **kwargs)
