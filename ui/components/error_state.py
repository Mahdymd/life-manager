"""ui/components/error_state.py — نمایش وضعیت خطا با دکمه‌ی تلاش مجدد.

طبق بخش ۹ اسپک: "ErrorState widgets" و Definition of Done بخش ۱۶:
"Error state with human-readable message and retry/recovery options".

ساختار این فایل عمداً از empty_state.py پیروی می‌کند (تا دو کامپوننت
خواهر ظاهر یکسانی داشته باشند)، با دو تفاوت: آیکون/رنگ پیش‌فرض قرمز
(danger) است، و دکمه پیش‌فرض «تلاش دوباره» نام دارد.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from ui.style.theme_manager import colors, Spacing
from ui.style.icons import icon as make_icon


class ErrorState(QWidget):
    """وضعیت خطا با پیام قابل‌فهم و دکمه‌ی تلاش مجدد.

    مثال:
        err = ErrorState("مشکلی در بارگذاری تسک‌ها پیش آمد.")
        err.retry_clicked.connect(self.refresh)
    """

    retry_clicked = Signal()

    def __init__(self, message: str = "مشکلی پیش آمد.",
                 detail: str = "", retry_text: str = "تلاش دوباره",
                 parent=None):
        super().__init__(parent)
        c = colors()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(Spacing.MD)
        layout.setContentsMargins(Spacing.XXL + Spacing.SM, Spacing.XXXL + Spacing.XXL,
                                   Spacing.XXL + Spacing.SM, Spacing.XXXL + Spacing.XXL)

        pix = make_icon("warning", 40, colors().danger).pixmap(40, 40)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(pix)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(message)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {c.danger}; background: transparent;")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        if detail:
            detail_lbl = QLabel(detail)
            detail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            detail_lbl.setStyleSheet(f"font-size: 12px; color: {c.text_secondary}; background: transparent;")
            detail_lbl.setWordWrap(True)
            layout.addWidget(detail_lbl)

        if retry_text:
            btn = QPushButton(retry_text)
            btn.setProperty("class", "outline")
            btn.setFixedWidth(160)
            btn.clicked.connect(self.retry_clicked)
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
