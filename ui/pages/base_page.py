"""ui/pages/base_page.py — کلاس پایه تمام صفحات."""

from typing import Callable, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from ui.style.theme_manager import colors, Spacing, Typography


class BasePage(QWidget):
    """هر صفحه از این کلاس ارث می‌برد.

    Empty/Loading/Error scaffolding (اختیاری):
    این کلاس یک لایه‌ی نمایش وضعیت روی محتوای صفحه فراهم می‌کند که با
    show_loading()/show_empty()/show_error()/show_content() کنترل
    می‌شود. کاملاً اختیاری و عقب‌سازگار است — self._content و
    self._content_layout دقیقاً مثل قبل کار می‌کنند و هیچ صفحه‌ی
    موجودی که این متدهای جدید را صدا نزند تغییری در رفتارش نمی‌بیند.

    مثال استفاده در یک صفحه‌ی جدید یا موجود:
        def refresh(self):
            self.show_loading()
            self._vm.load()  # بعداً وقتی data_changed/error_occurred
                              # سیگنال داد، show_content()/show_error()
                              # صدا زده می‌شود.
    """
    request_navigate = Signal(str)   # برای ناوبری از داخل صفحه

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(0)
        self._build_header()

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        self._content_layout.setSpacing(Spacing.XL - 4)

        # لایه‌ی state (اختیاری) — پیش‌فرض همیشه self._content نشان
        # داده می‌شود، دقیقاً مثل قبل از این تغییر.
        self._body_stack = QStackedWidget()
        self._body_stack.addWidget(self._content)
        self._state_widget: Optional[QWidget] = None
        self._root.addWidget(self._body_stack)

        self.setup_ui()

    def _build_header(self):
        self._header = QFrame()
        self._header.setObjectName("title-bar")
        self._header.setFixedHeight(64)
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(Spacing.XXL, 0, Spacing.XL, 0)
        self._title_lbl = QLabel("")
        self._title_lbl.setStyleSheet(Typography.H2.qss("background: transparent;"))
        self._subtitle_lbl = QLabel("")
        self._subtitle_lbl.setStyleSheet(
            Typography.CAPTION.qss(f"color: {colors().text_secondary}; background: transparent;"))
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(self._title_lbl)
        title_box.addWidget(self._subtitle_lbl)
        hl.addLayout(title_box)
        hl.addStretch()
        self._action_box = QHBoxLayout()
        self._action_box.setSpacing(8)
        hl.addLayout(self._action_box)
        self._root.addWidget(self._header)

    def set_header(self, title: str, subtitle: str = ""):
        self._title_lbl.setText(title)
        self._subtitle_lbl.setText(subtitle)
        self._subtitle_lbl.setVisible(bool(subtitle))

    def add_header_action(self, text: str, cls: str = "primary") -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("class", cls)
        self._action_box.addWidget(btn)
        return btn

    def setup_ui(self):
        """هر صفحه این متد را override می‌کند."""
        pass

    def refresh(self):
        """بارگذاری مجدد داده‌ها — هر صفحه override می‌کند."""
        pass

    # ────────────────────────────────────────────────────────────
    # Empty/Loading/Error scaffolding (اختیاری — بخش ۴ و ۱۶ اسپک:
    # "Never create a view without empty, loading, error ... states"،
    # "Always include placeholder/skeleton UI while data loads",
    # "Always implement empty states", "Always show human‑readable
    # error messages with retry/recovery options").
    # ────────────────────────────────────────────────────────────

    def _set_state_widget(self, widget: QWidget) -> None:
        if self._state_widget is not None:
            self._body_stack.removeWidget(self._state_widget)
            self._state_widget.deleteLater()
        self._state_widget = widget
        self._body_stack.addWidget(widget)
        self._body_stack.setCurrentWidget(widget)

    def show_content(self) -> None:
        """محتوای واقعی صفحه (self._content) را دوباره نمایش می‌دهد."""
        self._body_stack.setCurrentWidget(self._content)

    def show_loading(self, rows: int = 3) -> None:
        """یک SkeletonLoader ساده به‌جای محتوا نمایش می‌دهد، تا زمانی
        که داده‌ی async آماده شود و show_content() صدا زده شود."""
        from ui.components.skeleton_loader import SkeletonLoader
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        wl.addWidget(SkeletonLoader(rows=rows))
        wl.addStretch()
        self._set_state_widget(wrap)

    def show_empty(self, icon: str = "empty", title: str = "چیزی پیدا نشد",
                   description: str = "", action_text: str = "",
                   on_action: Optional[Callable[[], None]] = None) -> None:
        """وضعیت خالی با آیکون/پیام/دکمه‌ی اکشن اختیاری."""
        from ui.components.empty_state import EmptyState
        w = EmptyState(icon, title, description, action_text)
        if on_action:
            w.action_clicked.connect(on_action)
        self._set_state_widget(w)

    def show_error(self, message: str = "مشکلی پیش آمد.", detail: str = "",
                   on_retry: Optional[Callable[[], None]] = None) -> None:
        """وضعیت خطا با پیام قابل‌فهم و دکمه‌ی تلاش دوباره (پیش‌فرض:
        فراخوانی خودِ self.refresh)."""
        from ui.components.error_state import ErrorState
        w = ErrorState(message, detail)
        w.retry_clicked.connect(on_retry or self.refresh)
        self._set_state_widget(w)
