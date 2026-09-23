"""ui/components/stat_card.py — کارت‌های آماری داشبورد."""

from typing import Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from ui.style.theme_manager import colors, Spacing, Elevation


class StatCard(QFrame):
    """کارت آماری با آیکون، عنوان، مقدار، و توضیح."""

    def __init__(self, icon: str, title: str, value: str = "–",
                 subtitle: str = "", accent_color: Optional[str] = None,
                 parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        # اگر accent_color داده نشود، رنگ primary تم جاری استفاده می‌شود
        # (نه یک hex ثابت) تا در تم روشن/تاریک درست رندر شود.
        self._accent = accent_color or colors().primary
        self._setup_ui(icon, title, value, subtitle)
        Elevation.apply(self, Elevation.SM)

    def enterEvent(self, event) -> None:
        """طبق بخش ۹ اسپک: "subtle scale on cards" — به‌جای transform
        واقعی روی QWidget (که چیدمان بقیه‌ی صفحه را به‌هم می‌ریزد)، عمق
        سایه در حین hover افزایش می‌یابد؛ همان حس «کارت بالا می‌آید» را
        بدون ریسک لایوت می‌دهد."""
        Elevation.apply(self, Elevation.MD)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        Elevation.apply(self, Elevation.SM)
        super().leaveEvent(event)

    def _setup_ui(self, icon, title, value, subtitle):
        c = colors()
        self.setMinimumHeight(110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.XS + 2)

        top = QHBoxLayout()
        from ui.style.icons import icon as _icon
        icon_lbl = QLabel()
        icon_lbl.setPixmap(_icon(icon, 22, self._accent).pixmap(22, 22))
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 13px; color: {c.text_secondary}; background: transparent;")
        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        top.addStretch()
        layout.addLayout(top)

        self._value_lbl = QLabel(value)
        self._value_lbl.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {self._accent};
            background: transparent;
        """)
        layout.addWidget(self._value_lbl)

        if subtitle:
            self._sub_lbl = QLabel(subtitle)
            self._sub_lbl.setStyleSheet(f"font-size: 12px; color: {c.text_secondary}; background: transparent;")
        else:
            self._sub_lbl = QLabel("")
            self._sub_lbl.setVisible(False)
        layout.addWidget(self._sub_lbl)

    def update_value(self, value: str, subtitle: str = None):
        self._value_lbl.setText(value)
        if subtitle is not None:
            self._sub_lbl.setText(subtitle)
            self._sub_lbl.setVisible(True)


class MiniStatCard(QFrame):
    def __init__(self, label: str, value: str, color: Optional[str] = None, parent=None):
        super().__init__(parent)
        c = colors()
        self.setProperty("class", "card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD + 2, Spacing.SM + 2, Spacing.MD + 2, Spacing.SM + 2)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 12px; color: {c.text_secondary}; background: transparent;")
        self._val = QLabel(value)
        self._val.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {color or c.primary}; background: transparent;")
        layout.addWidget(lbl)
        layout.addStretch()
        layout.addWidget(self._val)

    def set_value(self, v: str):
        self._val.setText(v)
