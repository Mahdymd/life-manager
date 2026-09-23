"""tests/unit/test_task_service.py

طبق آیتم High #۳ از Audit: این تنها تست فعلی پروژه است — پایه‌ریزی
scaffolding واقعی pytest، نه پوشش کامل. مسیری که پوشش می‌دهد دقیقاً
همان مسیر بحرانی است که در همین نشست به core/services/task_service.py
اضافه شد (بخش ۷.۴ اسپک: "Atomic transactions for all writes"):

    complete_task() یک تسک تکرارشونده را هم done می‌کند و هم بلافاصله
    نسخه‌ی بعدی‌اش را می‌سازد — این دو نوشتن باید atomic باشند (یا هر
    دو انجام شوند، یا هیچ‌کدام)، نه دو commit جدا که بین‌شان ممکن است
    برنامه crash کند و یک تسکِ «تکمیل‌شده بدون نسخه‌ی بعدی» بماند.
"""

from core.domain.enums import TaskRecurrence, TaskStatus


def test_task_completion_creates_next(temp_db):
    from core.database.connection import get_connection
    from core.services import task_service

    task = task_service.create_task(
        "آب دادن به گل‌ها",
        due_date="2025-01-01",
        recurrence=TaskRecurrence.DAILY,
    )

    conn = get_connection()
    count_before = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]

    result = task_service.complete_task(task.id)
    assert result is True

    # ۱. تسک اصلی باید done شده باشد
    completed = task_service.get_task(task.id)
    assert completed is not None
    assert completed.status == TaskStatus.DONE
    assert completed.completed_at is not None

    # ۲. دقیقاً یک تسک جدید ساخته شده باشد (نه صفر، نه بیشتر)
    count_after = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
    assert count_after == count_before + 1

    # ۳. تسک جدید باید همان عنوان و یک روز جلوتر از تسک اصلی باشد
    next_task = conn.execute(
        "SELECT * FROM tasks WHERE title=? AND id != ?",
        (task.title, task.id),
    ).fetchone()
    assert next_task is not None
    assert next_task["due_date"] == "2025-01-02"
    assert next_task["status"] == "todo"


def test_task_completion_without_recurrence_does_not_spawn(temp_db):
    """تسک غیرتکرارشونده نباید هیچ نسخه‌ی بعدی‌ای بسازد — تضمین
    می‌کند تغییرات transaction رفتار مسیر عادی (non-recurring) را
    خراب نکرده باشد."""
    from core.database.connection import get_connection
    from core.services import task_service

    task = task_service.create_task(
        "یک‌بار خرید کن", due_date="2025-01-01",
        recurrence=TaskRecurrence.NONE,
    )

    conn = get_connection()
    count_before = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]

    assert task_service.complete_task(task.id) is True

    count_after = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
    assert count_after == count_before
