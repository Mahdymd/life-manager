"""core/services/undo_service.py — Undo Manager سراسری برنامه.

مطابق بخش ۷.۵ اسپک: "Undo manager capable of reverting last insert/
update/delete via inverse SQL or JSON patches."

طراحی:
- یک پشته‌ی محدود (deque با سقف ۵۰ عملیات) از "اقدام‌های معکوس"
  (inverse actions) نگه‌داری می‌شود. هر ViewModel پس از انجام یک عملیات
  مخرب/تغییردهنده، یک تابع inverse (undo_fn) را همراه با توضیح
  کاربرپسند (description، برای نمایش در Toast) روی این پشته push می‌کند.
- این ماژول به‌جای Qt (UI) مستقل است تا هم از سرویس‌ها و هم از
  ViewModel ها قابل استفاده باشد؛ ViewModel ها (از طریق BaseViewModel)
  یک wrapper نازک روی همین ماژول ارائه می‌دهند.
- برای entity هایی که Version History دارند (task, journal_entry —
  core/services/history_service.py)، undo_fn معمولاً فقط
  history_service.restore_snapshot(history_id) را صدا می‌زند؛ یعنی
  خودِ داده‌ی معکوس (snapshot) از قبل در دیتابیس ثبت شده و اینجا فقط
  یک اشاره‌گر (closure) به آن نگه‌داشته می‌شود — نه کپی مجدد داده.
- برای entity هایی که هنوز Version History ندارند (بقیه‌ی ماژول‌ها)،
  undo_fn می‌تواند مستقیماً یک closure با پارامترهای لازم برای INSERT
  مجدد یا بازگردانی مقدار قبلی باشد (JSON patch ساده به شکل kwargs).

این پشته session-scoped است (در حافظه، نه دیتابیس) — یعنی با بستن
برنامه ریست می‌شود؛ این دقیقاً همان چیزی است که "Toast (with undo
action)" (بخش ۹) نیاز دارد، نه یک سیستم time-travel دائمی (آن قابلیت
جدا توسط history_service پوشش داده شده است).
"""

from __future__ import annotations
import logging
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Optional

logger = logging.getLogger("life_manager.undo")

_MAX_STACK_SIZE = 50


@dataclass
class UndoAction:
    description: str            # مثلاً: "حذف تسک «خرید نان»"
    undo_fn: Callable[[], None]  # فراخوانی این تابع، عملیات را معکوس می‌کند


_stack: Deque[UndoAction] = deque(maxlen=_MAX_STACK_SIZE)


def push(description: str, undo_fn: Callable[[], None]) -> None:
    """یک اقدام معکوس جدید را روی پشته قرار می‌دهد.

    باید بلافاصله بعد از موفقیت عملیات اصلی (insert/update/delete)
    فراخوانی شود، معمولاً از callback موفقیت (on_success) در
    BaseViewModel.run_async که روی UI thread اجرا می‌شود.
    """
    _stack.append(UndoAction(description=description, undo_fn=undo_fn))
    logger.debug("Undo action pushed: %s (stack size=%d)", description, len(_stack))


def can_undo() -> bool:
    return len(_stack) > 0


def peek_description() -> Optional[str]:
    """توضیح آخرین اقدام قابل‌بازگشت را برمی‌گرداند (بدون pop کردن)،
    برای نمایش در متن دکمه‌ی Toast مثل «↩ بازگردانی حذف تسک»."""
    return _stack[-1].description if _stack else None


def undo() -> Optional[str]:
    """آخرین اقدام را معکوس می‌کند و توضیح آن را برمی‌گرداند (یا None
    اگر پشته خالی بود). اگر خودِ undo_fn خطا بدهد، exception بالا
    می‌رود تا caller (ViewModel) بتواند پیام خطای مناسب نمایش دهد —
    و چون قبلش از پشته pop شده، دوباره تلاش برای همان اقدام، خطای
    تکراری نمی‌دهد."""
    if not _stack:
        return None
    action = _stack.pop()
    try:
        action.undo_fn()
    except Exception:
        logger.error("Undo failed for action: %s", action.description, exc_info=True)
        raise
    logger.info("Undo executed: %s", action.description)
    return action.description


def clear() -> None:
    """پشته را کاملاً خالی می‌کند (مثلاً هنگام خروج از برنامه یا تغییر
    ماژول فعلی، تا undo از یک صفحه‌ی دیگر روی داده‌ی نامرتبط اجرا نشود)."""
    _stack.clear()
