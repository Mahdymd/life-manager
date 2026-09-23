"""ui/components/empty_state.py — نمایش وضعیت خالی."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from ui.style.theme_manager import colors, Spacing
from ui.style.icons import icon as make_icon


class EmptyState(QWidget):
    action_clicked = Signal()

    def __init__(self, icon: str = "empty", title: str = "چیزی پیدا نشد",
                 description: str = "", action_text: str = "",
                 parent=None):
        super().__init__(parent)
        c = colors()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(Spacing.MD)
        layout.setContentsMargins(Spacing.XXL + Spacing.SM, Spacing.XXXL + Spacing.XXL,
                                   Spacing.XXL + Spacing.SM, Spacing.XXXL + Spacing.XXL)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(make_icon(icon or "empty", 48, colors().text_secondary).pixmap(48, 48))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 600; background: transparent;")
        layout.addWidget(title_lbl)

        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_lbl.setStyleSheet(f"font-size: 13px; color: {c.text_secondary}; background: transparent;")
            desc_lbl.setWordWrap(True)
            layout.addWidget(desc_lbl)

        if action_text:
            btn = QPushButton(action_text)
            btn.setProperty("class", "primary")
            btn.setFixedWidth(160)
            btn.clicked.connect(self.action_clicked)
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
