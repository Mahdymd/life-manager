"""Regression tests for the Phase-10 runtime bugs found in the audit.

These cover repository/service paths that only fail once the database
has real rows (empty-DB smoke tests hid them).
"""

from datetime import date

from core.services import (
    task_service, goal_service, finance_service, focus_service, learning_service,
)
from core.database.connection import get_connection
from utils.date_utils import iran_weekday, weekday_name_fa, days_in_jalali_month, jalali_to_gregorian
import config


def test_task_stats_are_ints_not_none(temp_db):
    stats = task_service.get_task_stats()
    for key in ("total", "done", "todo", "in_progress", "due_today", "overdue"):
        assert key in stats
        assert isinstance(stats[key], int)
        assert stats[key] == 0

    today = date.today().isoformat()
    task_service.create_task("امروز", due_date=today)
    stats = task_service.get_task_stats()
    assert stats["total"] == 1
    assert stats["due_today"] == 1
    assert stats["todo"] == 1


def test_goal_key_results_do_not_crash(temp_db):
    g = goal_service.create_goal("تمام کردن پروژه", "quarterly")
    goal_service.upsert_key_result(g.id, title="ماژول‌ها", target=13, current=9, unit="ماژول")
    krs = goal_service.get_key_results(g.id)
    assert len(krs) == 1
    assert krs[0].unit == "ماژول"
    assert krs[0].target == 13


def test_budgets_do_not_crash_on_row_get(temp_db):
    conn = get_connection()
    cat = conn.execute(
        "INSERT INTO categories(module,name,created_at) VALUES('finance','غذا',?)",
        ("2026-01-01",),
    ).lastrowid
    from core.database.connection import commit
    commit()
    finance_service.upsert_budget(cat, 1_000_000, 80)
    budgets = finance_service.get_budgets()
    assert len(budgets) == 1
    assert budgets[0].category_name == "غذا"
    assert budgets[0].monthly_limit == 1_000_000


def test_saving_goal_inserts_into_saving_goals(temp_db):
    sid = finance_service.add_saving_goal("لپ‌تاپ", 80_000_000, current_amount=25_000_000)
    assert sid > 0
    conn = get_connection()
    row = conn.execute("SELECT * FROM saving_goals WHERE id=?", (sid,)).fetchone()
    assert row is not None
    assert row["title"] == "لپ‌تاپ"
    assert row["current_amount"] == 25_000_000
    # must NOT have been written into transactions
    tx_count = conn.execute("SELECT COUNT(*) AS c FROM transactions").fetchone()["c"]
    assert tx_count == 0


def test_focus_session_persists(temp_db):
    session = focus_service.start_session("pomodoro", 25)
    assert session.id > 0
    assert focus_service.complete_session(session.id, 25) is True
    stats = focus_service.get_focus_stats()
    assert stats["today_pomodoros"] == 1
    assert stats["today_focus_min"] == 25


def test_skills_row_get(temp_db):
    learning_service.add_skill("Python", level=4, target_level=5)
    skills = learning_service.get_skills()
    assert len(skills) == 1
    assert skills[0].name == "Python"
    assert skills[0].level == 4


def test_iran_weekday_saturday_start():
    # 1 مهر 1405 = 23 سپتامبر 2026 = چهارشنبه
    g = date(2026, 9, 23)
    assert jalali_to_gregorian(1405, 7, 1) == g
    assert iran_weekday(g) == 4
    assert weekday_name_fa(g) == "چهارشنبه"
    assert config.WEEKDAY_FA[0] == "شنبه"
    assert config.WEEKDAY_FA[4] == "چهارشنبه"
    # شنبه
    sat = date(2026, 9, 19)
    assert iran_weekday(sat) == 0
    assert weekday_name_fa(sat) == "شنبه"


def test_jalali_esfand_leap_and_common():
    # 1403 کبیسه است (اسفند ۳۰ روز)، 1404 معمولی (۲۹ روز)
    assert days_in_jalali_month(1403, 12) == 30
    assert days_in_jalali_month(1404, 12) == 29
    assert days_in_jalali_month(1405, 1) == 31
    assert days_in_jalali_month(1405, 7) == 30


def test_pyside_signal_int_keys_need_object():
    """PySide6 Signal(dict) silently drops dicts whose keys are ints."""
    from PySide6.QtCore import QObject, Signal, QCoreApplication
    app = QCoreApplication.instance() or QCoreApplication([])

    class Box(QObject):
        as_dict = Signal(dict)
        as_obj = Signal(object)

    box = Box()
    got = {}
    box.as_dict.connect(lambda d: got.__setitem__("dict", d))
    box.as_obj.connect(lambda d: got.__setitem__("obj", d))
    payload = {1: ["subtask"]}
    box.as_dict.emit(payload)
    box.as_obj.emit(payload)
    assert got.get("dict") in (None, {}), "Signal(dict) must drop int-key dicts"
    assert got.get("obj") == payload
