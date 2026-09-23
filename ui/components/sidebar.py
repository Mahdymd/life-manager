"""ui/components/sidebar.py — Sidebar ناوبری، بدون conflict با QSS.

Constitution: no emoji icons — uses ui.style.icons geometric set.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from ui.style.theme_manager import colors, Motion
from ui.style.icons import module_icon, icon
import config

NAV_ITEMS = [
    ("dashboard",  "داشبورد"),
    ("tasks",      "تسک‌ها"),
    ("goals",      "اهداف"),
    ("habits",     "عادت‌ها"),
    ("finance",    "مالی"),
    ("journal",    "روزانه"),
    ("notes",      "یادداشت"),
    ("focus",      "فوکوس"),
    ("health",     "سلامت"),
    ("learning",   "یادگیری"),
    ("calendar",   "تقویم"),
    ("analytics",  "آنالیتیکس"),
]

_CW = config.SIDEBAR_WIDTH    # 72 collapsed
_EW = config.SIDEBAR_EXPANDED # 224 expanded


class NavButton(QPushButton):
    def __init__(self, module: str, label: str, parent=None):
        super().__init__(parent)
        self.module = module
        self._label = label
        self.setProperty("class", "nav")
        self.setCheckable(True)
        self.setToolTip(label)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setAccessibleName(label)
        self._apply_collapsed()

    def _icon_for(self, size: int = 20):
        c = colors()
        col = c.primary if self.isChecked() else c.text_secondary
        return module_icon(self.module, size, col)

    def _apply_collapsed(self):
        self.setIcon(self._icon_for(22))
        self.setText("")
        self.setIconSize(self.icon().actualSize(self.icon().availableSizes()[0] if self.icon().availableSizes() else self.size()))
        from PySide6.QtCore import QSize
        self.setIconSize(QSize(22, 22))
        self.setMinimumSize(_CW - 16, 44)
        self.setMaximumSize(_CW - 16, 44)

    def _apply_expanded(self):
        self.setIcon(self._icon_for(20))
        from PySide6.QtCore import QSize
        self.setIconSize(QSize(20, 20))
        self.setText(f"  {self._label}")
        self.setMinimumSize(_EW - 16, 44)
        self.setMaximumSize(_EW - 16, 44)

    def set_expanded(self, expanded: bool):
        if expanded:
            self._apply_expanded()
        else:
            self._apply_collapsed()

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        # refresh icon colour for active state
        if self.maximumWidth() >= _EW - 16:
            self._apply_expanded()
        else:
            self._apply_collapsed()


class Sidebar(QWidget):
    module_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._expanded = False
        self._buttons: dict = {}
        self._anim = None
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumWidth(_CW)
        self.setMaximumWidth(_CW)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Toggle
        self._toggle = QPushButton()
        self._toggle.setProperty("class", "nav")
        self._toggle.setIcon(icon("menu", 22, colors().text_secondary))
        from PySide6.QtCore import QSize
        self._toggle.setIconSize(QSize(22, 22))
        self._toggle.setMinimumSize(_CW - 16, 44)
        self._toggle.setMaximumSize(_CW - 16, 44)
        self._toggle.setToolTip("باز/بسته کردن منو")
        self._toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle.setAccessibleName("باز و بسته کردن منو")
        self._toggle.clicked.connect(self._toggle_sidebar)
        layout.addWidget(self._toggle, 0, Qt.AlignmentFlag.AlignHCenter)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setMaximumHeight(1)
        sep.setStyleSheet(f"background:{colors().divider};border:none;")
        layout.addWidget(sep)
        layout.addSpacing(4)

        for module, label in NAV_ITEMS:
            btn = NavButton(module, label)
            btn.clicked.connect(lambda chk=False, m=module: self._on_click(m))
            self._buttons[module] = btn
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch()

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setMaximumHeight(1)
        sep2.setStyleSheet(f"background:{colors().divider};border:none;")
        layout.addWidget(sep2)
        layout.addSpacing(4)

        cfg_btn = NavButton("settings", "تنظیمات")
        cfg_btn.clicked.connect(lambda: self._on_click("settings"))
        self._buttons["settings"] = cfg_btn
        layout.addWidget(cfg_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        self.set_active("dashboard")

    def _on_click(self, module: str):
        self.set_active(module)
        self.module_changed.emit(module)

    def set_active(self, module: str):
        for k, btn in self._buttons.items():
            btn.setChecked(k == module)

    def _toggle_sidebar(self):
        self._expanded = not self._expanded
        target = _EW if self._expanded else _CW

        self._anim = QPropertyAnimation(self, b"maximumWidth")
        self._anim.setDuration(Motion.NORMAL)
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(target)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()
        self.setMinimumWidth(target)

        for btn in self._buttons.values():
            btn.set_expanded(self._expanded)

        from PySide6.QtCore import QSize
        if self._expanded:
            self._toggle.setIcon(icon("close", 20, colors().text_secondary))
            self._toggle.setIconSize(QSize(20, 20))
            self._toggle.setText("")
            self._toggle.setMinimumSize(_EW - 16, 44)
            self._toggle.setMaximumSize(_EW - 16, 44)
        else:
            self._toggle.setIcon(icon("menu", 22, colors().text_secondary))
            self._toggle.setIconSize(QSize(22, 22))
            self._toggle.setText("")
            self._toggle.setMinimumSize(_CW - 16, 44)
            self._toggle.setMaximumSize(_CW - 16, 44)
