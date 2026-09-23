"""ui/components/onboarding_overlay.py — راهنمای سه‌مرحله‌ای اولین اجرا (Phase 8).

طبق بخش ۱۳ اسپک: "Onboarding: 3‑step guided overlay on first launch".

این یک overlay مودال‌مانند است (فرزند پنجره‌ی اصلی، نه QDialog جدا) که
روی کل محتوای برنامه می‌نشیند؛ سه مرحله دارد: خوش‌آمدگویی، معرفی
ماژول‌های اصلی، و میان‌برهای کلیدی — طبق تصمیم طراحی، به‌جای «spotlight»
زنده روی ویجت‌های واقعی (که پیاده‌سازی‌اش بدون تست تعاملی زنده پرخطر
است)، یک کارت مرکزی سه‌مرحله‌ای ساده و قابل‌اطمینان است.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

from ui.style.theme_manager import colors, Spacing, Radius, Elevation

_STEPS = [
    {
        "icon": "smile",
        "title": "به Life Manager خوش اومدی",
        "body": "یک اپ کاملاً آفلاین برای مدیریت تسک‌ها، عادت‌ها، اهداف، "
                "مالی، و یادداشت‌های روزانه‌ات — همه‌چیز فقط روی سیستم خودت ذخیره می‌شه.",
    },
    {
        "icon": "compass",
        "title": "همه‌چیز از سایدبار در دسترسه",
        "body": "از سایدبار سمت راست می‌تونی بین ۱۲ ماژول (تسک، عادت، هدف، مالی، "
                "یادداشت روزانه، تقویم، فوکوس، آنالیتیکس و ...) جابه‌جا بشی.",
    },
    {
        "icon": "keyboard",
        "title": "کارها رو سریع‌تر انجام بده",
        "body": "Ctrl+K برای باز کردن Command Palette (جستجوی سراسری)، "
                "Ctrl+N برای افزودن سریع، و Ctrl+Shift+N برای یادداشت شناور آنی.",
    },
]


class OnboardingOverlay(QWidget):
    """Overlay سه‌مرحله‌ای روی کل پنجره‌ی اصلی.

    Signals:
        finished(): بعد از اتمام یا رد کردن (Skip) کل راهنما.

    مثال:
        overlay = OnboardingOverlay(main_window)
        overlay.finished.connect(mark_onboarding_completed)
        overlay.show_over_parent()
    """

    finished = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._step = 0
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        c = colors()
        # پس‌زمینه‌ی نیمه‌شفاف تیره روی کل پنجره (backdrop) — طبق بخش ۹
        # اسپک: "Modals fade in with backdrop blur" (Qt Widgets بلور
        # واقعی ندارد؛ نزدیک‌ترین معادل قابل‌اتکا یک overlay نیمه‌شفاف است)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 140);")

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card = QWidget()
        self._card.setFixedWidth(420)
        self._card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._card.setStyleSheet(f"""
            background-color: {c.surface_elev};
            border: 1px solid {c.border};
            border-radius: {Radius.XL}px;
        """)
        Elevation.apply(self._card, Elevation.XL)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(Spacing.XXL, Spacing.XXL, Spacing.XXL, Spacing.XL)
        card_layout.setSpacing(Spacing.MD)

        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent;")
        card_layout.addWidget(self._icon_lbl)

        self._title_lbl = QLabel()
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setStyleSheet("font-size: 17px; font-weight: 700; background: transparent;")
        card_layout.addWidget(self._title_lbl)

        self._body_lbl = QLabel()
        self._body_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._body_lbl.setWordWrap(True)
        self._body_lbl.setStyleSheet(f"font-size: 13px; color: {c.text_secondary}; background: transparent;")
        card_layout.addWidget(self._body_lbl)

        self._dots_row = QHBoxLayout()
        self._dots_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dots_row.setSpacing(Spacing.XS)
        self._dot_labels = []
        for _ in _STEPS:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {c.border}; background: transparent; font-size: 12px;")
            self._dot_labels.append(dot)
            self._dots_row.addWidget(dot)
        card_layout.addLayout(self._dots_row)

        btn_row = QHBoxLayout()
        skip_btn = QPushButton("رد کردن")
        skip_btn.setProperty("class", "ghost")
        skip_btn.clicked.connect(self._finish)
        self._next_btn = QPushButton("بعدی")
        self._next_btn.setProperty("class", "primary")
        self._next_btn.clicked.connect(self._go_next)
        btn_row.addWidget(skip_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._next_btn)
        card_layout.addLayout(btn_row)

        outer.addWidget(self._card)
        self._render_step()

    def _render_step(self) -> None:
        from ui.style.icons import icon as _icon
        c = colors()
        step = _STEPS[self._step]
        self._icon_lbl.setPixmap(_icon(step["icon"], 48, c.primary).pixmap(48, 48))
        self._title_lbl.setText(step["title"])
        self._body_lbl.setText(step["body"])
        for i, dot in enumerate(self._dot_labels):
            dot.setStyleSheet(
                f"color: {c.primary if i == self._step else c.border}; "
                f"background: transparent; font-size: 12px;"
            )
        is_last = self._step == len(_STEPS) - 1
        self._next_btn.setText("شروع کن" if is_last else "بعدی")

    def _go_next(self) -> None:
        if self._step >= len(_STEPS) - 1:
            self._finish()
            return
        self._step += 1
        self._render_step()

    def _finish(self) -> None:
        self.hide()
        self.finished.emit()

    def show_over_parent(self) -> None:
        if self.parent():
            self.setGeometry(self.parent().rect())
        self._step = 0
        self._render_step()
        self.show()
        self.raise_()

    def resizeEvent(self, event) -> None:
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)
