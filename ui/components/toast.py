"""
ui/components/toast.py — اعلان شناور Toast (Phase 4).

طبق بخش ۹ اسپک: "Toast (with undo action)" و بخش ۱۴:
"toasts slide from top‑right with progress bar".

این کامپوننت جایگزین راه‌حل موقتی است که قبلاً در tasks_page.py برای
نمایش پیام «بازگردانده شد» از subtitle هدر صفحه استفاده می‌شد.

استفاده:
    from ui.components.toast import show_toast
    show_toast(self, "حذف تسک بازگردانده شد", action_text="واگرد",
               on_action=lambda: self._vm.undo_last())

نکته‌ی معماری: show_toast یک تابع سطح-ماژول است (نه متد صفحه) تا هر
View بدون نیاز به ساخت دستی ویجت، فقط یک خط صدا بزند — دقیقاً مثل
confirm() در confirm_dialog.py.
"""

from __future__ import annotations
from typing import Callable, Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve

from ui.style.theme_manager import colors, Spacing, Radius, Elevation, Motion


class Toast(QWidget):
    """اعلان شناور با پیام، دکمه‌ی اقدام اختیاری (مثل Undo)، و نوار
    پیشرفت شمارش‌معکوس. خودش را بعد از duration_ms با انیمیشن محو می‌کند.
    """

    def __init__(
        self,
        parent: QWidget,
        message: str,
        action_text: Optional[str] = None,
        on_action: Optional[Callable[[], None]] = None,
        duration_ms: int = 4000,
        icon: Optional[str] = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowFlags(Qt.WindowType.Widget)  # child overlay، نه پنجره‌ی جدا
        self._duration_ms = duration_ms

        c = colors()
        self.setStyleSheet(f"""
            Toast {{
                background-color: {c.surface_elev};
                border: 1px solid {c.border};
                border-radius: {Radius.LG}px;
            }}
        """)
        Elevation.apply(self, Elevation.LG)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        row = QHBoxLayout()
        row.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.MD, Spacing.MD)
        row.setSpacing(Spacing.MD)

        if icon:
            from ui.style.icons import icon as _icon_fn
            icon_lbl = QLabel()
            icon_lbl.setPixmap(_icon_fn(icon, 16, c.text_secondary).pixmap(16, 16))
            row.addWidget(icon_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"color: {c.text_primary}; font-size: 13px; background: transparent;")
        row.addWidget(msg_lbl, 1)

        if action_text and on_action:
            action_btn = QPushButton(action_text)
            action_btn.setProperty("class", "ghost")
            action_btn.setCursor(Qt.CursorShape.PointingHandCursor)

            def _on_click():
                on_action()
                self.dismiss()

            action_btn.clicked.connect(_on_click)
            row.addWidget(action_btn)

        close_btn = QPushButton("×")
        close_btn.setProperty("class", "icon")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.dismiss)
        row.addWidget(close_btn)

        outer.addLayout(row)

        self._progress = QProgressBar()
        self._progress.setRange(0, duration_ms)
        self._progress.setValue(duration_ms)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(3)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background: transparent; border: none; }}
            QProgressBar::chunk {{ background-color: {c.primary}; border-radius: 0px; }}
        """)
        outer.addWidget(self._progress)

        self.setFixedWidth(340)
        self.adjustSize()

        # شمارش‌معکوس بصری (progress bar) — با یک تایمر تیک‌تیک، نه
        # صرفاً یک QTimer.singleShot، تا کاربر پیشرفت را ببیند
        self._elapsed = 0
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start(50)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._fade_in = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_in.setDuration(Motion.NORMAL)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._fade_out = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_out.setDuration(Motion.NORMAL)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out.finished.connect(self.deleteLater)

    def _on_tick(self) -> None:
        self._elapsed += 50
        remaining = max(0, self._duration_ms - self._elapsed)
        self._progress.setValue(remaining)
        if remaining <= 0:
            self.dismiss()

    def show_animated(self) -> None:
        self.show()
        self._fade_in.start()

    def dismiss(self) -> None:
        self._tick_timer.stop()
        self._fade_out.start()


def show_toast(
    parent: QWidget,
    message: str,
    action_text: Optional[str] = None,
    on_action: Optional[Callable[[], None]] = None,
    duration_ms: int = 4000,
    icon: Optional[str] = None,
) -> Toast:
    """یک Toast در گوشه‌ی بالا-راست پنجره‌ی parent نمایش می‌دهد.

    parent باید یک صفحه/ویجت قابل‌مشاهده باشد (مثلاً self در یک
    BasePage)؛ Toast به‌عنوان overlay روی window آن صفحه قرار می‌گیرد.

    icon: نام آیکون از ui/style/icons.py (اختیاری، مثلاً "check",
    "clock", "award") که قبل از متن نمایش داده می‌شود.
    """
    window = parent.window()
    toast = Toast(window, message, action_text, on_action, duration_ms, icon)
    margin = Spacing.LG
    x = window.width() - toast.width() - margin
    y = margin + 50  # کمی پایین‌تر از هدر، تا با breadcrumb/search تداخل نکند
    toast.move(max(0, x), y)
    toast.raise_()
    toast.show_animated()
    return toast
