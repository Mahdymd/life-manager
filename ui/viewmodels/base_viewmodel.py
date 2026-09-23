"""
ui/viewmodels/base_viewmodel.py

کلاس پایه‌ی تمام ViewModel ها.
مطابق Phase 3 اسپک: ViewModel ها state را نگه می‌دارند، View ها فقط observe
می‌کنند (signal/slot). هیچ ViewModel ای نباید از هیچ کلاس Qt Widget مطلع
باشد؛ فقط QObject برای signal ها.

قانون حیاتی: هیچ متد این کلاس یا فرزندانش نباید عملیات دیتابیس/سرویس را
مستقیم و synchronous روی همان thread فراخوانی کننده اجرا کند. همه از طریق
run_async روی یک Worker/QThread اجرا می‌شوند (utils/thread_worker.py) تا
UI thread هرگز بلاک نشود.
"""

from __future__ import annotations
import logging
from typing import Any, Callable, Optional
from PySide6.QtCore import QObject, Signal

from utils.thread_worker import Worker
from core.domain.exceptions import AppError
from core.services import undo_service

logger = logging.getLogger("life_manager.viewmodel")


class BaseViewModel(QObject):
    """پایه مشترک همه ViewModel ها.

    Signals:
        loading_changed(bool): وقتی یک عملیات async شروع/تمام می‌شود.
        error_occurred(str): پیام خطای قابل‌نمایش به کاربر (فارسی، بدون stacktrace).
        undo_available_changed(bool): وقتی امکان undo فعال/غیرفعال می‌شود
            (برای فعال/غیرفعال کردن دکمه‌ی Undo یا میان‌بر Ctrl+Z در View).
        undo_performed(str): بعد از اجرای موفق undo، با توضیح اقدامی که
            معکوس شد (برای نمایش در Toast، مثلاً «حذف تسک بازگردانده شد»).
    """

    loading_changed = Signal(bool)
    error_occurred = Signal(str)
    undo_available_changed = Signal(bool)
    undo_performed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._is_loading: bool = False
        self._active_workers: list[Worker] = []

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    def _set_loading(self, value: bool) -> None:
        if self._is_loading != value:
            self._is_loading = value
            self.loading_changed.emit(value)

    def run_async(
        self,
        fn: Callable[..., Any],
        on_success: Optional[Callable[[Any], None]] = None,
        *args: Any,
        on_error: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> Worker:
        """
        fn را روی یک QThread جدا اجرا می‌کند و نتیجه را از طریق signal به
        UI thread برمی‌گرداند. هرگز مستقیم fn را صدا نزنید.

        - fn: تابع سرویس/ریپازیتوری که باید اجرا شود (خودِ fn در worker
          thread اجرا می‌شود، پس نباید هیچ ویجتی را لمس کند).
        - on_success: callback که با نتیجه‌ی fn روی UI thread فراخوانی
          می‌شود (چون QueuedConnection پیش‌فرض signal/slot بین thread ها
          این تضمین را می‌دهد).
        - on_error: callback اختصاصی خطا؛ اگر ندهید از error_occurred
          استفاده می‌شود.
        """
        worker = Worker(fn, *args, **kwargs)
        self._active_workers.append(worker)

        def _cleanup() -> None:
            if worker in self._active_workers:
                self._active_workers.remove(worker)

        def _handle_success(result: Any) -> None:
            self._set_loading(False)
            if on_success:
                on_success(result)
            _cleanup()

        def _handle_error(message: str) -> None:
            self._set_loading(False)
            logger.error("ViewModel async error in %s: %s", fn, message)
            friendly = self._to_friendly_message(message)
            if on_error:
                on_error(friendly)
            else:
                self.error_occurred.emit(friendly)
            _cleanup()

        worker.signals.finished.connect(_handle_success)
        worker.signals.error.connect(_handle_error)
        self._set_loading(True)
        worker.start()
        return worker

    @staticmethod
    def _to_friendly_message(raw: str) -> str:
        """پیام خطای خام را به پیام قابل‌فهم برای کاربر تبدیل می‌کند.
        AppError ها معمولاً خودشان پیام فارسی مناسب دارند؛ خطاهای ناشناخته
        را به یک پیام عمومی تبدیل می‌کنیم تا جزئیات فنی به کاربر درز نکند.
        """
        if not raw:
            return "خطای ناشناخته‌ای رخ داد."
        # اگر پیام از AppError آمده باشد (شکل "[CODE] message")، بخش پیام را نشان بده
        if raw.startswith("[") and "]" in raw:
            return raw.split("]", 1)[1].strip()
        return "مشکلی پیش آمد. لطفاً دوباره تلاش کنید."

    # ────────────────────────────────────────────────────────────
    # Undo/Redo — پوسته‌ی نازک روی core.services.undo_service (سراسری).
    # هر ViewModel با فراخوانی push_undo بعد از یک عملیات مخرب موفق،
    # امکان Ctrl+Z / دکمه‌ی Undo در Toast را رایگان به دست می‌آورد.
    # ────────────────────────────────────────────────────────────
    def push_undo(self, description: str, undo_fn: Callable[[], None]) -> None:
        """اقدام معکوس را روی پشته‌ی سراسری undo ثبت می‌کند و View را از
        فعال‌شدن امکان Undo باخبر می‌کند.

        باید فقط از داخل on_success (یعنی بعد از موفقیت قطعی عملیات
        اصلی در دیتابیس) فراخوانی شود، نه قبل از آن.
        """
        undo_service.push(description, undo_fn)
        self.undo_available_changed.emit(True)

    @property
    def can_undo(self) -> bool:
        return undo_service.can_undo()

    def peek_undo_description(self) -> Optional[str]:
        """توضیح آخرین اقدام قابل‌بازگشت را برمی‌گرداند، بدون اجرای undo —
        برای نمایش فوری یک Toast اقدام‌پذیر («حذف تسک X — واگرد») درست
        بعد از ثبت‌شدن خودِ اقدام مخرب، نه فقط بعد از اجرای undo."""
        return undo_service.peek_description()

    def undo_last(self) -> None:
        """آخرین اقدام قابل‌بازگشت را معکوس می‌کند (به‌صورت async، چون
        undo_fn معمولاً یک عملیات دیتابیسی است — مثل
        history_service.restore_snapshot). بعد از اتمام، سیگنال
        undo_performed با توضیح اقدام emit می‌شود تا View بتواند Toast
        نمایش دهد و لیست را دوباره refresh کند."""
        if not undo_service.can_undo():
            return

        def _do_undo() -> Optional[str]:
            return undo_service.undo()

        def _on_undone(description: Optional[str]) -> None:
            self.undo_available_changed.emit(undo_service.can_undo())
            if description:
                self.undo_performed.emit(description)

        self.run_async(_do_undo, _on_undone)

    def dispose(self) -> None:
        """باید هنگام بسته‌شدن صفحه/View فراخوانی شود تا worker های در حال
        اجرا به‌درستی متوقف و signal ها قطع شوند (جلوگیری از leak)."""
        for worker in list(self._active_workers):
            try:
                worker.signals.finished.disconnect()
                worker.signals.error.disconnect()
            except (RuntimeError, TypeError):
                pass
            if worker.isRunning():
                worker.quit()
                worker.wait(2000)
        self._active_workers.clear()
