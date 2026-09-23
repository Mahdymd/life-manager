"""ui/pages/notes_page.py — یادداشت‌ها / Knowledge Base."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QTextEdit, QLineEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QDialog, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from ui.pages.base_page import BasePage
from ui.components.confirm_dialog import confirm
from ui.style.theme_manager import colors
from ui.viewmodels.note_list_viewmodel import NoteListViewModel


class NotesPage(BasePage):
    """View خالص — بدون import مستقیم از core.services؛ همه چیز از طریق
    self._vm (NoteListViewModel)."""

    def setup_ui(self):
        self._vm = NoteListViewModel(self)
        self._vm.notes_changed.connect(self._on_notes_changed)
        self._vm.note_created.connect(self._on_note_created)
        self._vm.error_occurred.connect(self._show_error)

        self.set_header("یادداشت‌ها", "Knowledge Base شخصی")
        add_btn = self.add_header_action("+ یادداشت جدید")
        add_btn.clicked.connect(lambda: self._new_note())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        self._content_layout.addWidget(splitter)

        # ── Tree panel ──
        left = QFrame()
        left.setProperty("class", "card")
        left.setMaximumWidth(260)
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(10, 10, 10, 10)
        left_l.setSpacing(8)

        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("جستجو...")
        from ui.style.icons import icon as _icon
        self._search.addAction(_icon("search", 15, colors().text_secondary),
                               QLineEdit.ActionPosition.LeadingPosition)
        self._search.textChanged.connect(self._on_search)
        search_row.addWidget(self._search)
        left_l.addLayout(search_row)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setFrameShape(QFrame.Shape.NoFrame)
        self._tree.itemClicked.connect(self._on_select)
        left_l.addWidget(self._tree)
        splitter.addWidget(left)

        # ── Editor panel ──
        right = QFrame()
        right.setProperty("class", "card")
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(20, 16, 20, 16)
        right_l.setSpacing(10)

        title_row = QHBoxLayout()
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("عنوان یادداشت...")
        self._title_edit.setStyleSheet(
            "font-size:18px;font-weight:600;border:none;background:transparent;"
            f"border-bottom:1px solid {colors().border};border-radius:0;padding:4px 0;")
        self._pin_btn = QPushButton()
        self._pin_btn.setIcon(_icon("pin", 14, colors().text_secondary))
        self._pin_btn.setProperty("class", "icon")
        self._pin_btn.setToolTip("پین کردن")
        self._pin_btn.clicked.connect(self._toggle_pin)
        self._del_btn = QPushButton()
        self._del_btn.setIcon(_icon("trash", 14, colors().danger))
        self._del_btn.setProperty("class", "icon")
        self._del_btn.setToolTip("حذف")
        self._del_btn.clicked.connect(self._delete_current)
        title_row.addWidget(self._title_edit)
        title_row.addWidget(self._pin_btn)
        title_row.addWidget(self._del_btn)
        right_l.addLayout(title_row)

        self._editor = QTextEdit()
        self._editor.setPlaceholderText("محتوا را اینجا بنویسید (از Markdown پشتیبانی می‌شود)...")
        self._editor.setFrameShape(QFrame.Shape.NoFrame)
        right_l.addWidget(self._editor)

        save_row = QHBoxLayout()
        save_row.addStretch()
        self._save_btn = QPushButton("ذخیره")
        self._save_btn.setProperty("class", "primary")
        self._save_btn.clicked.connect(self._save)
        save_row.addWidget(self._save_btn)
        right_l.addLayout(save_row)

        splitter.addWidget(right)
        splitter.setSizes([240, 560])

        self._current_note = None
        self._auto_save = QTimer(self)
        self._auto_save.setSingleShot(True)
        self._auto_save.timeout.connect(self._save)
        self._title_edit.textChanged.connect(lambda: self._auto_save.start(2000))
        self._editor.textChanged.connect(lambda: self._auto_save.start(2000))
        self.refresh()

    def refresh(self):
        self._vm.load()

    def _on_notes_changed(self, notes: list):
        from ui.style.icons import icon as _icon2
        self._tree.clear()
        for note in notes:
            item = QTreeWidgetItem([note.title])
            item.setIcon(0, _icon2("pin" if note.is_pinned else "note",
                                   13, colors().primary if note.is_pinned else colors().text_disabled))
            item.setData(0, Qt.ItemDataRole.UserRole, note)
            self._tree.addTopLevelItem(item)

    def _on_select(self, item, col):
        note = item.data(0, Qt.ItemDataRole.UserRole)
        if note:
            self._current_note = note
            self._title_edit.blockSignals(True)
            self._editor.blockSignals(True)
            self._title_edit.setText(note.title)
            self._editor.setPlainText(note.content or "")
            self._title_edit.blockSignals(False)
            self._editor.blockSignals(False)

    def _open_form(self, *args, **kwargs):
        self._new_note()

    def _new_note(self):
        self._vm.create("یادداشت جدید")

    def _on_note_created(self, note):
        self._current_note = note
        self._title_edit.setText(note.title)
        self._editor.clear()

    def _save(self):
        if not self._current_note:
            return
        self._vm.update(
            self._current_note.id,
            title=self._title_edit.text().strip() or "بدون عنوان",
            content=self._editor.toPlainText(),
        )

    def _toggle_pin(self):
        if self._current_note:
            self._vm.toggle_pin(self._current_note.id)

    def _delete_current(self):
        if not self._current_note:
            return
        if confirm(self, "حذف یادداشت",
                   f"آیا از حذف «{self._current_note.title}» مطمئن هستید؟",
                   "حذف", danger=True):
            self._vm.remove(self._current_note.id)
            self._current_note = None
            self._title_edit.clear()
            self._editor.clear()

    def _on_search(self, query: str):
        self._vm.load(query)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
