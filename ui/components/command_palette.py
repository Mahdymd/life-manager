"""ui/components/command_palette.py — Command Palette با Ctrl+K."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeySequence, QFont
from typing import Callable, List, Dict, Any
from ui.style.theme_manager import colors, Radius

_MAX_RECENT_SEARCHES = 8


class CommandPalette(QDialog):
    command_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog)
        
        self._commands: List[Dict] = []
        self._recent_searches: List[str] = self._load_recent_searches()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._setup_ui()
        self._register_defaults()

    # ────────────────────────────────────────────────────────────
    # جستجوهای اخیر (پایدار، از طریق SettingsManager) — طبق بخش ۱۲
    # اسپک: "Search: FTS5 global search, results grouped by type,
    # recent searches stored."
    # ────────────────────────────────────────────────────────────
    @staticmethod
    def _load_recent_searches() -> List[str]:
        from core.services.settings_manager import get_settings_manager
        return get_settings_manager().recent_searches(_MAX_RECENT_SEARCHES)

    def _save_recent_searches(self) -> None:
        from core.services.settings_manager import get_settings_manager
        get_settings_manager().set_recent_searches(self._recent_searches)

    def _record_recent_search(self, query: str) -> None:
        query = query.strip()
        if not query or len(query) < 2:
            return
        # حذف تکراری قبلی (اگر بود) و قرار دادن در ابتدای لیست
        self._recent_searches = [q for q in self._recent_searches if q != query]
        self._recent_searches.insert(0, query)
        self._recent_searches = self._recent_searches[:_MAX_RECENT_SEARCHES]
        self._save_recent_searches()

    def _setup_ui(self):
        self.setMinimumWidth(600)
        self.setMaximumHeight(500)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        c = colors()
        container = QFrame()
        container.setObjectName("palette-container")
        container.setStyleSheet(f"""
            QFrame#palette-container {{
                border-radius: {Radius.XL}px;
                border: 1px solid {c.border};
            }}
        """)
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        self._search = QLineEdit()
        self._search.setPlaceholderText("جستجو یا دستور... (Ctrl+K)")
        self._search.setMinimumHeight(52)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                border-bottom: 1px solid {c.border};
                border-radius: {Radius.XL}px {Radius.XL}px 0 0;
                padding: 0 20px;
                font-size: 16px;
            }}
        """)
        self._search.textChanged.connect(self._on_search_changed)
        cl.addWidget(self._search)

        self._list = QListWidget()
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setStyleSheet(
            f"QListWidget {{ border: none; border-radius: 0 0 {Radius.XL}px {Radius.XL}px; }}"
        )
        self._list.itemActivated.connect(self._on_item_activated)
        self._list.setMinimumHeight(200)
        cl.addWidget(self._list)

        layout.addWidget(container)

    def _register_defaults(self):
        from ui.style.icons import MODULE_ICONS
        self._commands = [
            {"icon_name": MODULE_ICONS["tasks"], "title": "تسک جدید", "action": "new_task", "module": "tasks"},
            {"icon_name": MODULE_ICONS["goals"], "title": "هدف جدید", "action": "new_goal", "module": "goals"},
            {"icon_name": MODULE_ICONS["habits"], "title": "عادت جدید", "action": "new_habit", "module": "habits"},
            {"icon_name": MODULE_ICONS["finance"], "title": "تراکنش جدید", "action": "new_transaction", "module": "finance"},
            {"icon_name": MODULE_ICONS["journal"], "title": "یادداشت روزانه", "action": "open_journal", "module": "journal"},
            {"icon_name": MODULE_ICONS["focus"], "title": "شروع Pomodoro", "action": "start_pomodoro", "module": "focus"},
            {"icon_name": MODULE_ICONS["dashboard"], "title": "برو به داشبورد", "action": "navigate", "module": "dashboard"},
            {"icon_name": MODULE_ICONS["learning"], "title": "برو به یادگیری", "action": "navigate", "module": "learning"},
            {"icon_name": MODULE_ICONS["calendar"], "title": "برو به تقویم", "action": "navigate", "module": "calendar"},
            {"icon_name": MODULE_ICONS["analytics"], "title": "برو به آنالیتیکس", "action": "navigate", "module": "analytics"},
            {"icon_name": MODULE_ICONS["settings"], "title": "تنظیمات", "action": "navigate", "module": "settings"},
            {"icon_name": "save", "title": "بکاپ دستی", "action": "manual_backup", "module": "settings"},
        ]
        self._show_all()

    def _show_all(self):
        from ui.style.icons import icon
        self._list.clear()
        if self._recent_searches:
            header = QListWidgetItem("جستجوهای اخیر")
            header.setIcon(icon("clock", 14, colors().text_disabled))
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            self._list.addItem(header)
            for query in self._recent_searches:
                item = QListWidgetItem(f"  {query}")
                item.setIcon(icon("search", 14, colors().text_secondary))
                item.setData(Qt.ItemDataRole.UserRole, {"action": "recent_search", "query": query})
                self._list.addItem(item)
            sep = QListWidgetItem("─" * 20)
            sep.setFlags(Qt.ItemFlag.NoItemFlags)
            self._list.addItem(sep)
        for cmd in self._commands[:10]:
            item = QListWidgetItem(f"  {cmd['title']}")
            item.setIcon(icon(cmd["icon_name"], 16, colors().text_secondary))
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            item.setSizeHint(item.sizeHint().__class__(0, 44))
            self._list.addItem(item)

    def _on_search_changed(self, text: str):
        self._search_timer.start(100)

    def _do_search(self):
        from ui.style.icons import icon
        q = self._search.text().strip().lower()
        self._list.clear()
        if not q:
            self._show_all()
            return
        for cmd in self._commands:
            if q in cmd["title"].lower():
                item = QListWidgetItem(f"  {cmd['title']}")
                item.setIcon(icon(cmd["icon_name"], 16, colors().text_secondary))
                item.setData(Qt.ItemDataRole.UserRole, cmd)
                self._list.addItem(item)

        # جستجو در داده
        try:
            from core.services.search_service import global_search
            results = global_search(self._search.text())
            for r in results:
                snip = r.get("snippet") or ""
                label = f"  {r['title']}  ({r['type']})"
                if snip:
                    label += f"  —  {snip}"
                item = QListWidgetItem(label)
                item.setIcon(icon("search", 14, colors().text_secondary))
                item.setData(Qt.ItemDataRole.UserRole, {"action":"navigate",
                                                         "module":r["module"],"id":r["id"]})
                self._list.addItem(item)
        except Exception:
            pass

    def _on_item_activated(self, item: QListWidgetItem):
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if not cmd:
            return
        if cmd.get("action") == "recent_search":
            self._search.setText(cmd["query"])
            self._do_search()
            return
        if "id" in cmd:  # نتیجه‌ی جستجوی واقعی (نه دستور ثابت پیش‌فرض)
            self._record_recent_search(self._search.text())
        self.command_selected.emit(cmd)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            items = self._list.selectedItems()
            if items:
                self._on_item_activated(items[0])
            elif self._list.count() > 0:
                self._on_item_activated(self._list.item(0))
        elif event.key() == Qt.Key.Key_Down:
            cur = self._list.currentRow()
            self._list.setCurrentRow(min(cur+1, self._list.count()-1))
        elif event.key() == Qt.Key.Key_Up:
            cur = self._list.currentRow()
            self._list.setCurrentRow(max(cur-1, 0))
        else:
            super().keyPressEvent(event)

    def show_palette(self):
        self._search.clear()
        self._show_all()
        self._list.setCurrentRow(0)
        # center on parent
        if self.parent():
            p = self.parent().geometry()
            x = p.x() + (p.width() - self.width()) // 2
            y = p.y() + int(p.height() * 0.2)
            self.move(x, y)
        self.show()
        self._search.setFocus()
