"""
ui/viewmodels/task_list_viewmodel.py

ViewModel صفحه‌ی تسک‌ها. تمام state (لیست تسک‌ها، آمار، فیلترها) اینجا
نگه‌داری می‌شود. View (tasks_page.py) فقط این ViewModel را observe می‌کند
و هیچ import مستقیمی از core.services ندارد.

این فایل به‌عنوان نمونه‌ی مرجع (pilot) برای Phase 3 (اصلاح معماری MVVM)
پیاده‌سازی شده و الگوی آن باید برای بقیه صفحات (habits, goals, finance, ...)
تکرار شود.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.domain.models import Task
from core.services import history_service
from core.services.task_service import (
    get_all_tasks,
    get_today_tasks,
    get_overdue_tasks,
    get_task_stats,
    get_task,
    get_subtasks,
    create_task,
    update_task,
    complete_task,
    delete_task,
)


def _fetch_subtasks(parent_ids: List[int]) -> Dict[int, List[Task]]:
    """در worker thread اجرا می‌شود؛ زیرتسک‌های همه‌ی تسک‌های سطح‌بالای
    بارگذاری‌شده را یک‌جا می‌گیرد (نه یک‌به‌یک هنگام expand — برای
    سادگی و چون تعداد تسک‌های یک صفحه معمولاً کوچک است)."""
    result: Dict[int, List[Task]] = {}
    for pid in parent_ids:
        subs = get_subtasks(pid)
        if subs:
            result[pid] = subs
    return result


class TaskListViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی تسک‌ها.

    Signals:
        tasks_changed(list[Task]): هر بار لیست تسک‌های قابل‌نمایش عوض شود.
        stats_changed(dict): هر بار آمار (کل/امروز/معوقه/انجام‌شده) عوض شود.
    """

    tasks_changed = Signal(list)
    stats_changed = Signal(dict)
    categories_changed = Signal(list)
    subtasks_changed = Signal(dict)
    history_loaded = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tasks: List[Task] = []
        self._stats: Dict = {}
        self._categories: List = []
        self._status_filter: Optional[str] = None
        self._priority_filter: Optional[str] = None
        self._search: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Public read-only state (برای دسترسی سریع View بدون منتظر signal)
    # ------------------------------------------------------------------ #
    @property
    def tasks(self) -> List[Task]:
        return self._tasks

    @property
    def stats(self) -> Dict:
        return self._stats

    @property
    def categories(self) -> List:
        return self._categories

    def load_categories(self) -> None:
        """دسته‌بندی‌های تسک را async بارگذاری می‌کند — برای پر کردن
        combo box در TaskFormDialog، بدون اینکه دیالوگ مستقیم به
        core.database وصل شود."""
        self.run_async(self._fetch_categories, self._on_categories_loaded)

    @staticmethod
    def _fetch_categories() -> List:
        from core.repositories.tag_repository import TagRepository
        rows = TagRepository().get_category_all("task")
        return [{"id": r["id"], "name": r["name"]} for r in rows]

    def _on_categories_loaded(self, categories: List) -> None:
        self._categories = categories
        self.categories_changed.emit(categories)

    # ------------------------------------------------------------------ #
    # Filters
    # ------------------------------------------------------------------ #
    def set_status_filter(self, value: Optional[str]) -> None:
        self._status_filter = value or None
        self.load()

    def set_priority_filter(self, value: Optional[str]) -> None:
        self._priority_filter = value or None
        self.load()

    def set_search(self, text: Optional[str]) -> None:
        self._search = text.strip() if text and text.strip() else None
        self.load()

    # ------------------------------------------------------------------ #
    # Loading (async, هرگز UI thread را بلاک نمی‌کند)
    # ------------------------------------------------------------------ #
    def load(self) -> None:
        """آمار و لیست تسک‌ها را (هر دو async) بازخوانی می‌کند."""
        self.run_async(get_task_stats, self._on_stats_loaded)
        self.run_async(
            self._fetch_filtered_tasks,
            self._on_tasks_loaded,
            status=self._status_filter,
            priority=self._priority_filter,
            search=self._search,
        )

    @staticmethod
    def _fetch_filtered_tasks(
        status: Optional[str], priority: Optional[str], search: Optional[str]
    ) -> List[Task]:
        """این متد داخل worker thread اجرا می‌شود؛ فقط منطق داده، بدون Qt widget."""
        if status == "overdue":
            tasks = get_overdue_tasks()
        elif status == "today":
            tasks = get_today_tasks()
        else:
            tasks = get_all_tasks(status=status, search=search)
        if priority:
            tasks = [t for t in tasks if t.priority.value == priority]
        return tasks

    def _on_stats_loaded(self, stats: Dict) -> None:
        self._stats = stats
        self.stats_changed.emit(stats)

    def _on_tasks_loaded(self, tasks: List[Task]) -> None:
        self._tasks = tasks
        self.tasks_changed.emit(tasks)
        if tasks:
            parent_ids = [t.id for t in tasks]
            self.run_async(_fetch_subtasks, self.subtasks_changed.emit, parent_ids)

    def create_subtask(self, parent_id: int, title: str, **data) -> None:
        """طبق بخش ۴ اسپک: "Tasks: ... subtasks"."""
        self.run_async(
            create_task, lambda _r: self.load(),
            title=title, parent_task_id=parent_id, **data,
        )

    # ------------------------------------------------------------------ #
    # Mutations — همه async؛ در صورت موفقیت خودشان load() را دوباره صدا می‌زنند
    # ------------------------------------------------------------------ #
    def create(self, **data) -> None:
        self.run_async(create_task, lambda _result: self.load(), **data)

    def update(self, id_: int, **data) -> None:
        self.run_async(update_task, lambda _result: self.load(), id_, **data)

    def toggle_complete(self, id_: int) -> None:
        def _toggle() -> bool:
            task = get_task(id_)
            if not task:
                return False
            if task.status.value == "done":
                return update_task(id_, status="todo", completed_at=None)
            return complete_task(id_)

        self.run_async(_toggle, lambda _result: self.load())

    def remove(self, id_: int) -> None:
        """حذف تسک — با پشتیبانی کامل از Undo.

        چون TaskRepository.delete() از قبل (Phase 2) قبل از حذف واقعی،
        یک snapshot در entity_history ثبت می‌کند، اینجا فقط کافیست بعد
        از موفقیت حذف، جدیدترین ورودی تاریخچه را پیدا کرده و undo_fn را
        به یک فراخوانی ساده‌ی history_service.restore_snapshot گره بزنیم
        — یعنی هیچ کپی دستی از داده در ViewModel نگه‌داری نمی‌شود.
        """
        def _delete_with_capture():
            task = get_task(id_)
            title = task.title if task else "تسک"
            delete_task(id_)
            hist = history_service.get_history("task", id_, limit=1)
            history_id = hist[0].id if hist else None
            return title, history_id

        def _on_deleted(result) -> None:
            title, history_id = result
            if history_id is not None:
                self.push_undo(
                    f"حذف تسک «{title}»",
                    lambda: history_service.restore_snapshot(history_id),
                )
            self.load()

        self.run_async(_delete_with_capture, _on_deleted)

    def fetch_task_for_edit(self, id_: int, on_loaded) -> None:
        """برای باز کردن دیالوگ ویرایش: تسک را async می‌خواند و از طریق
        callback به View برمی‌گرداند (View هرگز مستقیم get_task صدا نمی‌زند)."""
        self.run_async(get_task, on_loaded, id_)

    # ────────────────────────────────────────────────────────────
    # Version History — طبق بخش ۶ اسپک: "Version History: restore
    # previous versions of tasks/journal entries"
    # ────────────────────────────────────────────────────────────
    def load_history(self, task_id: int) -> None:
        self.run_async(
            history_service.get_history, self.history_loaded.emit, "task", task_id)

    def restore_from_history(self, history_id: int) -> None:
        self.run_async(history_service.restore_snapshot, lambda _r: self.load(), history_id)
