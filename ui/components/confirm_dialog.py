"""ui/components/confirm_dialog.py — دیالوگ تأیید عملیات."""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from ui.style.theme_manager import colors, Spacing, Radius


class ConfirmDialog(QDialog):
    def __init__(self, title: str, message: str,
                 confirm_text: str = "تأیید", danger: bool = False,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setMinimumWidth(380)
        self._setup_ui(title, message, confirm_text, danger)

    def _setup_ui(self, title, message, confirm_text, danger):
        c = colors()
        self.setStyleSheet(
            f"QDialog {{ border-radius: {Radius.LG}px; border: 1px solid {c.border}; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        t = QLabel(title)
        t.setStyleSheet("font-size: 16px; font-weight: 700; background: transparent;")
        layout.addWidget(t)

        m = QLabel(message)
        m.setStyleSheet(f"font-size: 13px; color: {c.text_secondary}; background: transparent;")
        m.setWordWrap(True)
        layout.addWidget(m)

        btns = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.clicked.connect(self.reject)
        confirm = QPushButton(confirm_text)
        confirm.setProperty("class", "danger" if danger else "primary")
        confirm.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(confirm)
        layout.addLayout(btns)


def confirm(parent, title: str, message: str,
            confirm_text: str = "تأیید", danger: bool = False) -> bool:
    dlg = ConfirmDialog(title, message, confirm_text, danger, parent)
    return dlg.exec() == QDialog.DialogCode.Accepted
