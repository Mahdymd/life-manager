"""ui/components/drawer.py — پنل کشویی از لبه‌ی صفحه (Phase 4).

طبق بخش ۹ اسپک: "Dialog, Drawer (custom overlay)".

برخلاف Toast (که خودکار محو می‌شود)، Drawer باز می‌ماند تا کاربر آن را
ببندد — برای فرم‌های جزئی/فیلترهای پیشرفته که نمی‌خواهیم کل صفحه را
مثل QDialog مسدود کنند اما هم‌زمان باید روی محتوا شناور باشند.

پیاده‌سازی به‌عنوان یک ویجت فرزند parent (نه QDialog جدا) تا بتواند
با انیمیشن از لبه‌ی راست/چپ اسلاید شود؛ QDialog های واقعی Qt به این
شکل انیمیت نمی‌شوند.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal

from ui.style.theme_manager import colors, Spacing, Radius, Elevation, Motion


class Drawer(QWidget):
    """پنل کشویی از لبه‌ی راست (پیش‌فرض) یا چپ صفحه.

    Signals:
        closed(): وقتی درور کاملاً بسته و مخفی شد.

    مثال:
        drawer = Drawer(self.window(), title="فیلترهای پیشرفته", width=340)
        drawer.body.addWidget(my_filter_form)
        drawer.open()
    """

    closed = Signal()

    def __init__(
        self,
        parent: QWidget,
        title: str = "",
        width: int = 360,
        side: str = "right",
        parent_widget: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent_widget or parent)
        self._host = parent
        self._panel_width = width
        self._side = side
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        c = colors()
        self.setStyleSheet(f"""
            Drawer {{
                background-color: {c.surface};
                border-{'left' if side == 'right' else 'right'}: 1px solid {c.border};
            }}
        """)
        Elevation.apply(self, Elevation.LG)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.MD, Spacing.MD)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        header.addWidget(title_lbl)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setProperty("class", "icon")
        close_btn.clicked.connect(self.close_drawer)
        header.addWidget(close_btn)
        outer.addLayout(header)

        body_container = QWidget()
        self.body = QVBoxLayout(body_container)
        self.body.setContentsMargins(Spacing.LG, 0, Spacing.LG, Spacing.LG)
        self.body.setSpacing(Spacing.MD)
        outer.addWidget(body_container, 1)

        self.hide()
        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(Motion.NORMAL)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _target_geometry(self, visible: bool) -> QRect:
        host_h = self._host.height()
        if self._side == "right":
            x_visible = self._host.width() - self._panel_width
            x = x_visible if visible else self._host.width()
        else:
            x_visible = 0
            x = x_visible if visible else -self._panel_width
        return QRect(x, 0, self._panel_width, host_h)

    def open(self) -> None:
        self.setGeometry(self._target_geometry(False))
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(self._target_geometry(False))
        self._anim.setEndValue(self._target_geometry(True))
        self._anim.start()

    def close_drawer(self) -> None:
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(self._target_geometry(False))
        try:
            self._anim.finished.disconnect()
        except (RuntimeError, TypeError):
            pass
        self._anim.finished.connect(self._on_closed)
        self._anim.start()

    def _on_closed(self) -> None:
        self.hide()
        self.closed.emit()
