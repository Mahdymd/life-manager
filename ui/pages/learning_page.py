"""ui/pages/learning_page.py — صفحه یادگیری (کتاب، دوره، مهارت)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QComboBox, QDialog, QFormLayout,
    QSpinBox, QTextEdit, QTabWidget, QScrollArea, QProgressBar,
    QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt
from ui.pages.base_page import BasePage
from ui.components.empty_state import EmptyState
from ui.components.confirm_dialog import confirm
from ui.style.theme_manager import colors
from ui.viewmodels.learning_viewmodel import LearningViewModel


class BookFormDialog(QDialog):
    def __init__(self, parent=None, book=None):
        super().__init__(parent)
        self.setWindowTitle("کتاب جدید" if not book else "ویرایش کتاب")
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setMinimumWidth(420)
        self._book = book
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        from ui.style.icons import icon as _icon
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(8)
        hdr_icon_lbl = QLabel()
        hdr_icon_lbl.setPixmap(_icon("learning", 18, colors().text_primary).pixmap(18, 18))
        hdr_row.addWidget(hdr_icon_lbl)
        hdr = QLabel(self.windowTitle())
        hdr.setStyleSheet("font-size:17px;font-weight:700;background:transparent;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        form = QFormLayout()
        form.setSpacing(10)
        self._title = QLineEdit()
        form.addRow("عنوان *:", self._title)
        self._author = QLineEdit()
        form.addRow("نویسنده:", self._author)
        self._status = QComboBox()
        self._status.addItem("می‌خوام بخونم", "want")
        self._status.addItem("در حال خواندن", "reading")
        self._status.addItem("خوانده‌شده", "done")
        self._status.addItem("رهاشده", "abandoned")
        form.addRow("وضعیت:", self._status)
        self._pages = QSpinBox()
        self._pages.setRange(0, 10000)
        form.addRow("تعداد صفحات:", self._pages)
        self._category = QLineEdit()
        self._category.setPlaceholderText("مثال: رمان، خودیاری، فنی")
        form.addRow("دسته‌بندی:", self._category)
        layout.addLayout(form)

        if book:
            self._title.setText(book.title)
            self._author.setText(book.author or "")
            idx = self._status.findData(book.status.value)
            if idx >= 0: self._status.setCurrentIndex(idx)
            self._pages.setValue(book.total_pages or 0)
            self._category.setText(book.category or "")

        btns = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.clicked.connect(self.reject)
        save = QPushButton("ذخیره")
        save.setProperty("class", "primary")
        save.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _save(self):
        if not self._title.text().strip():
            self._title.setFocus()
            return
        self.accept()

    def get_data(self):
        return {
            "title": self._title.text().strip(),
            "author": self._author.text().strip() or None,
            "status": self._status.currentData(),
            "total_pages": self._pages.value() or None,
            "category": self._category.text().strip() or None,
        }


class CourseFormDialog(QDialog):
    def __init__(self, parent=None, course=None):
        super().__init__(parent)
        self.setWindowTitle("دوره جدید" if not course else "ویرایش دوره")
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setMinimumWidth(420)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        from ui.style.icons import icon as _icon2
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(8)
        hdr_icon_lbl = QLabel()
        hdr_icon_lbl.setPixmap(_icon2("learning", 18, colors().text_primary).pixmap(18, 18))
        hdr_row.addWidget(hdr_icon_lbl)
        hdr = QLabel(self.windowTitle())
        hdr.setStyleSheet("font-size:17px;font-weight:700;background:transparent;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        form = QFormLayout()
        self._title = QLineEdit()
        form.addRow("عنوان *:", self._title)
        self._platform = QLineEdit()
        self._platform.setPlaceholderText("مثال: یوتیوب، Udemy")
        form.addRow("پلتفرم:", self._platform)
        self._status = QComboBox()
        self._status.addItem("می‌خوام شروع کنم", "want")
        self._status.addItem("در حال گذراندن", "in_progress")
        self._status.addItem("تمام‌شده", "done")
        self._status.addItem("رهاشده", "abandoned")
        form.addRow("وضعیت:", self._status)
        self._lessons = QSpinBox()
        self._lessons.setRange(0, 1000)
        form.addRow("تعداد جلسات:", self._lessons)
        layout.addLayout(form)

        if course:
            self._title.setText(course.title)
            self._platform.setText(course.platform or "")
            idx = self._status.findData(course.status.value)
            if idx >= 0: self._status.setCurrentIndex(idx)
            self._lessons.setValue(course.total_lessons or 0)

        btns = QHBoxLayout()
        cancel = QPushButton("انصراف")
        cancel.clicked.connect(self.reject)
        save = QPushButton("ذخیره")
        save.setProperty("class", "primary")
        save.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _save(self):
        if not self._title.text().strip():
            self._title.setFocus()
            return
        self.accept()

    def get_data(self):
        return {
            "title": self._title.text().strip(),
            "platform": self._platform.text().strip() or None,
            "status": self._status.currentData(),
            "total_lessons": self._lessons.value() or None,
        }


class BookCard(QFrame):
    def __init__(self, book, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.book = book
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        top = QHBoxLayout()
        tc = colors()
        status_colors = {"want":tc.text_secondary,"reading":tc.warning,"done":tc.success,"abandoned":tc.danger}
        status_labels = {"want":"می‌خوام بخونم","reading":"در حال خواندن","done":"خوانده‌شده","abandoned":"رهاشده"}
        c = status_colors.get(book.status.value, tc.text_secondary)
        badge = QLabel(status_labels.get(book.status.value, ""))
        badge.setStyleSheet(f"background:{c}22;color:{c};border-radius:8px;padding:2px 8px;font-size:10px;font-weight:600;")
        top.addWidget(badge)
        top.addStretch()
        from ui.style.icons import icon as _icon3
        edit_btn = QPushButton(); edit_btn.setProperty("class","icon")
        edit_btn.setIcon(_icon3("edit", 13, tc.text_secondary))
        edit_btn.setToolTip("ویرایش")
        edit_btn.clicked.connect(lambda: on_edit(book))
        del_btn = QPushButton(); del_btn.setProperty("class","icon")
        del_btn.setIcon(_icon3("trash", 13, tc.danger))
        del_btn.setToolTip("حذف")
        del_btn.clicked.connect(lambda: on_delete(book))
        top.addWidget(edit_btn); top.addWidget(del_btn)
        layout.addLayout(top)

        title = QLabel(book.title)
        title.setStyleSheet("font-size:14px;font-weight:600;background:transparent;")
        title.setWordWrap(True)
        layout.addWidget(title)
        if book.author:
            author = QLabel(book.author)
            author.setStyleSheet(f"font-size:12px;color:{tc.text_secondary};background:transparent;")
            layout.addWidget(author)
        if book.total_pages:
            pb = QProgressBar()
            pb.setRange(0, book.total_pages)
            pb.setValue(book.current_page)
            pb.setFixedHeight(5)
            layout.addWidget(pb)


class CourseCard(QFrame):
    def __init__(self, course, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.course = course
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        top = QHBoxLayout()
        tc = colors()
        status_colors = {"want":tc.text_secondary,"in_progress":tc.warning,"done":tc.success,"abandoned":tc.danger}
        status_labels = {"want":"می‌خوام شروع کنم","in_progress":"در حال گذراندن","done":"تمام‌شده","abandoned":"رهاشده"}
        c = status_colors.get(course.status.value, tc.text_secondary)
        badge = QLabel(status_labels.get(course.status.value, ""))
        badge.setStyleSheet(f"background:{c}22;color:{c};border-radius:8px;padding:2px 8px;font-size:10px;font-weight:600;")
        top.addWidget(badge)
        top.addStretch()
        from ui.style.icons import icon as _icon4
        edit_btn = QPushButton(); edit_btn.setProperty("class","icon")
        edit_btn.setIcon(_icon4("edit", 13, tc.text_secondary))
        edit_btn.setToolTip("ویرایش")
        edit_btn.clicked.connect(lambda: on_edit(course))
        del_btn = QPushButton(); del_btn.setProperty("class","icon")
        del_btn.setIcon(_icon4("trash", 13, tc.danger))
        del_btn.setToolTip("حذف")
        del_btn.clicked.connect(lambda: on_delete(course))
        top.addWidget(edit_btn); top.addWidget(del_btn)
        layout.addLayout(top)

        title = QLabel(course.title)
        title.setStyleSheet("font-size:14px;font-weight:600;background:transparent;")
        title.setWordWrap(True)
        layout.addWidget(title)
        if course.platform:
            plat = QLabel(course.platform)
            plat.setStyleSheet(f"font-size:12px;color:{tc.text_secondary};background:transparent;")
            layout.addWidget(plat)
        if course.total_lessons:
            pb = QProgressBar()
            pb.setRange(0, course.total_lessons)
            pb.setValue(course.done_lessons)
            pb.setFixedHeight(5)
            layout.addWidget(pb)


class LearningPage(BasePage):
    """View خالص — بدون import مستقیم از core.services؛ همه چیز از طریق
    self._vm (LearningViewModel)."""

    def setup_ui(self):
        self._vm = LearningViewModel(self)
        self._vm.books_changed.connect(self._on_books_changed)
        self._vm.courses_changed.connect(self._on_courses_changed)
        self._vm.error_occurred.connect(self._show_error)

        self.set_header("یادگیری", "کتاب‌ها، دوره‌ها و مهارت‌ها")

        tabs = QTabWidget()
        self._content_layout.addWidget(tabs)

        # Books tab
        books_tab = QWidget()
        books_l = QVBoxLayout(books_tab)
        books_hdr = QHBoxLayout()
        books_hdr.addStretch()
        add_book_btn = QPushButton("+ کتاب جدید")
        add_book_btn.setProperty("class", "primary")
        add_book_btn.clicked.connect(lambda: self._open_book_form())
        books_hdr.addWidget(add_book_btn)
        books_l.addLayout(books_hdr)
        books_scroll = QScrollArea()
        books_scroll.setWidgetResizable(True)
        books_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._books_grid_widget = QWidget()
        self._books_grid = QGridLayout(self._books_grid_widget)
        self._books_grid.setSpacing(12)
        books_scroll.setWidget(self._books_grid_widget)
        books_l.addWidget(books_scroll)
        from ui.style.icons import icon as _icon5
        tabs.addTab(books_tab, _icon5("learning", 15, colors().text_secondary), "کتاب‌ها")

        # Courses tab
        courses_tab = QWidget()
        courses_l = QVBoxLayout(courses_tab)
        courses_hdr = QHBoxLayout()
        courses_hdr.addStretch()
        add_course_btn = QPushButton("+ دوره جدید")
        add_course_btn.setProperty("class", "primary")
        add_course_btn.clicked.connect(lambda: self._open_course_form())
        courses_hdr.addWidget(add_course_btn)
        courses_l.addLayout(courses_hdr)
        courses_scroll = QScrollArea()
        courses_scroll.setWidgetResizable(True)
        courses_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._courses_grid_widget = QWidget()
        self._courses_grid = QGridLayout(self._courses_grid_widget)
        self._courses_grid.setSpacing(12)
        courses_scroll.setWidget(self._courses_grid_widget)
        courses_l.addWidget(courses_scroll)
        tabs.addTab(courses_tab, _icon5("learning", 15, colors().text_secondary), "دوره‌ها")

        self.refresh()

    def refresh(self):
        self._vm.load()

    def _on_books_changed(self, books: list):
        while self._books_grid.count():
            item = self._books_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, book in enumerate(books):
            card = BookCard(book, self._open_book_form, self._delete_book)
            self._books_grid.addWidget(card, i // 3, i % 3)

    def _on_courses_changed(self, courses: list):
        while self._courses_grid.count():
            item = self._courses_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, course in enumerate(courses):
            card = CourseCard(course, self._open_course_form, self._delete_course)
            self._courses_grid.addWidget(card, i // 3, i % 3)

    def _open_form(self, *args, **kwargs):
        self._open_book_form()

    def _open_book_form(self, book=None):
        dlg = BookFormDialog(self, book)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if book:
                self._vm.update_book(book.id, **data)
            else:
                self._vm.add_book(**data)

    def _delete_book(self, book):
        if confirm(self, "حذف کتاب", f"آیا از حذف «{book.title}» مطمئن هستید؟", "حذف", danger=True):
            self._vm.remove_book(book.id)

    def _open_course_form(self, course=None):
        dlg = CourseFormDialog(self, course)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if course:
                self._vm.update_course(course.id, **data)
            else:
                self._vm.add_course(**data)

    def _delete_course(self, course):
        if confirm(self, "حذف دوره", f"آیا از حذف «{course.title}» مطمئن هستید؟", "حذف", danger=True):
            self._vm.remove_course(course.id)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
