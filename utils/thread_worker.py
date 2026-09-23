"""utils/thread_worker.py — QThread wrapper برای عملیات سنگین."""

from typing import Callable, Any
from PySide6.QtCore import QThread, Signal, QObject


class WorkerSignals(QObject):
    finished = Signal(object)   # نتیجه
    error    = Signal(str)      # پیام خطا
    progress = Signal(int)      # ۰–۱۰۰


class Worker(QThread):
    """یک callable را در thread جداگانه اجرا می‌کند."""

    def __init__(self, fn: Callable, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))
