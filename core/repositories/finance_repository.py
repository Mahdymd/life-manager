"""core/repositories/finance_repository.py"""

from typing import List, Optional, Dict, Tuple
from core.repositories.base_repository import BaseRepository
from core.domain.models import Transaction, Budget, SavingGoal
from core.domain.enums import TransactionType


class FinanceRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("transactions")

    def _row_to_tx(self, row) -> Transaction:
        d = self._row_to_dict(row)
        return Transaction(
            id=d["id"], type=TransactionType(d["type"]), amount=d["amount"],
            date=d["date"], category_id=d.get("category_id"), note=d.get("note"),
            goal_id=d.get("goal_id"), is_recurring=bool(d.get("is_recurring",0)),
            recur_config=d.get("recur_config"),
            created_at=d["created_at"], updated_at=d["updated_at"],
            category_name=d.get("category_name"),
        )

    def get_transactions(self, month: str = None, type_: str = None,
                         category_id: int = None, search: str = None,
                         limit: int = None) -> List[Transaction]:
        wheres, params = [], []
        if month: wheres.append("t.date LIKE ?"); params.append(f"{month}%")
        if type_: wheres.append("t.type=?"); params.append(type_)
        if category_id: wheres.append("t.category_id=?"); params.append(category_id)
        if search: wheres.append("t.note LIKE ?"); params.append(f"%{search}%")
        where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
        limit_sql = f"LIMIT {limit}" if limit else ""
        rows = self._fetch_all(f"""
            SELECT t.*, c.name AS category_name FROM transactions t
            LEFT JOIN categories c ON c.id=t.category_id
            {where_sql} ORDER BY t.date DESC, t.id DESC {limit_sql}""", tuple(params))
        return [self._row_to_tx(r) for r in rows]

    def add(self, type_: str, amount: float, date: str, **kwargs) -> Transaction:
        id_ = self._insert({"type": type_, "amount": amount, "date": date, **kwargs})
        row = self._fetch_one("""
            SELECT t.*, c.name AS category_name FROM transactions t
            LEFT JOIN categories c ON c.id=t.category_id WHERE t.id=?""", (id_,))
        return self._row_to_tx(row)

    def update(self, id_: int, **kwargs) -> bool:
        return self._update(id_, kwargs)

    def get_summary(self, month: str) -> Dict:
        row = self._fetch_one("""
            SELECT
              SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS income,
              SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense
            FROM transactions WHERE date LIKE ?""", (f"{month}%",))
        d = dict(row) if row else {"income": 0, "expense": 0}
        d["income"]  = d["income"]  or 0
        d["expense"] = d["expense"] or 0
        d["balance"] = d["income"] - d["expense"]
        return d

    def get_expense_by_category(self, month: str) -> List[Tuple]:
        rows = self._fetch_all("""
            SELECT c.name, SUM(t.amount) AS total
            FROM transactions t LEFT JOIN categories c ON c.id=t.category_id
            WHERE t.type='expense' AND t.date LIKE ?
            GROUP BY t.category_id ORDER BY total DESC""", (f"{month}%",))
        return [(r["name"] or "متفرقه", r["total"]) for r in rows]

    def get_monthly_trend(self, months: int = 6) -> List[Dict]:
        rows = self._fetch_all("""
            SELECT strftime('%Y-%m', date) AS month,
              SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS income,
              SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense
            FROM transactions
            GROUP BY month ORDER BY month DESC LIMIT ?""", (months,))
        return [dict(r) for r in reversed(rows)]

    # ── Budgets ──
    def get_budgets(self) -> List[Budget]:
        rows = self._fetch_all("""
            SELECT b.*, c.name AS category_name FROM budgets b
            LEFT JOIN categories c ON c.id=b.category_id ORDER BY c.name""")
        result = []
        for r in rows:
            d = self._row_to_dict(r)
            result.append(Budget(
                id=d["id"], category_id=d["category_id"],
                monthly_limit=d["monthly_limit"], alert_at_pct=d["alert_at_pct"],
                created_at=d["created_at"], updated_at=d["updated_at"],
                category_name=d.get("category_name"),
            ))
        return result

    def upsert_budget(self, category_id: int, monthly_limit: float,
                      alert_at_pct: int = 85) -> None:
        now = self._now()
        self._conn().execute("""
            INSERT INTO budgets(category_id,monthly_limit,alert_at_pct,created_at,updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(category_id) DO UPDATE
            SET monthly_limit=?,alert_at_pct=?,updated_at=?""",
            (category_id, monthly_limit, alert_at_pct, now, now,
             monthly_limit, alert_at_pct, now))
        from core.database.connection import commit
        commit()

    # ── Saving Goals ──
    def get_saving_goals(self) -> List[SavingGoal]:
        rows = self._fetch_all(
            "SELECT * FROM saving_goals WHERE status='active' ORDER BY created_at")
        result = []
        for r in rows:
            d = self._row_to_dict(r)
            result.append(SavingGoal(
                id=d["id"], title=d["title"], target_amount=d["target_amount"],
                current_amount=d["current_amount"], target_date=d.get("target_date"),
                goal_id=d.get("goal_id"), status=d["status"],
                created_at=d["created_at"], updated_at=d["updated_at"],
            ))
        return result

    def add_saving_goal(self, title: str, target_amount: float, **kwargs) -> int:
        # جدول این repository «transactions» است؛ _insert این‌جا اشتباه می‌رود.
        now = self._now()
        cur = self._conn().execute(
            """INSERT INTO saving_goals
               (title, target_amount, current_amount, target_date, goal_id,
                status, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (title, target_amount,
             kwargs.get("current_amount", 0) or 0,
             kwargs.get("target_date"),
             kwargs.get("goal_id"),
             kwargs.get("status", "active"),
             now, now),
        )
        from core.database.connection import commit
        commit()
        return cur.lastrowid

    def update_saving_goal(self, id_: int, **kwargs) -> bool:
        cur = self._conn().execute(
            f"UPDATE saving_goals SET {', '.join(f'{k}=?' for k in kwargs)}, updated_at=? WHERE id=?",
            (*kwargs.values(), self._now(), id_))
        from core.database.connection import commit
        commit()
        return cur.rowcount > 0
