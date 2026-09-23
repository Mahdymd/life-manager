"""ui/components/base_menu.py — BaseMenu و ContextMenu (Phase 4).

طبق بخش ۹ اسپک: "BaseMenu, ContextMenu".

ظاهر QMenu از قبل در QSS مرکزی تعریف شده (رنگ/hover/separator)؛ این
فایل فقط یک API راحت برای ساخت منو با لیستی از (متن, callback) اضافه
می‌کند تا کد صفحات به‌جای تکرار `menu.addAction(...)` دستی، یک‌خطی شود.
"""

from __future__ import annotations
from typing import Callable, List, Optional, Tuple
from PySide6.QtWidgets import QMenu, QWidget
from PySide6.QtGui import QAction


MenuItem = Tuple[str, Optional[Callable[[], None]]]


class BaseMenu(QMenu):
    """منوی استاندارد برنامه.

    مثال:
        menu = BaseMenu(items=[
            ("ویرایش", self._edit),
            ("---", None),          # جداکننده
            ("حذف", self._delete),
        ])
        menu.exec(pos)
    """

    def __init__(self, items: Optional[List[MenuItem]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        if items:
            self.populate(items)

    def populate(self, items: List[MenuItem]) -> None:
        for text, callback in items:
            if text == "---":
                self.addSeparator()
                continue
            action = QAction(text, self)
            if callback:
                action.triggered.connect(callback)
            self.addAction(action)


class ContextMenu(BaseMenu):
    """منوی راست‌کلیک — همان BaseMenu، فقط نام‌گذاری صریح برای موارد
    استفاده‌ی contextMenuEvent/customContextMenuRequested.

    مثال:
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos: ContextMenu([("حذف", self._delete)]).exec(widget.mapToGlobal(pos))
        )
    """
    pass
