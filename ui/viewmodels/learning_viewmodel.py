"""
ui/viewmodels/learning_viewmodel.py

ViewModel صفحه‌ی یادگیری (کتاب/دوره). الگو از task_list_viewmodel.py.
"""

from __future__ import annotations
from typing import List
from PySide6.QtCore import Signal

from ui.viewmodels.base_viewmodel import BaseViewModel
from core.domain.models import Book, Course
from core.services.learning_service import (
    get_books,
    add_book,
    update_book,
    delete_book,
    get_courses,
    add_course,
    update_course,
    delete_course,
)


class LearningViewModel(BaseViewModel):
    """State و business-orchestration صفحه‌ی یادگیری.

    Signals:
        books_changed(list[Book])
        courses_changed(list[Course])
    """

    books_changed = Signal(list)
    courses_changed = Signal(list)

    def load(self) -> None:
        self.run_async(get_books, self._on_books_loaded)
        self.run_async(get_courses, self._on_courses_loaded)

    def _on_books_loaded(self, books: List[Book]) -> None:
        self.books_changed.emit(books)

    def _on_courses_loaded(self, courses: List[Course]) -> None:
        self.courses_changed.emit(courses)

    def add_book(self, **data) -> None:
        self.run_async(add_book, lambda _r: self.load(), **data)

    def update_book(self, id_: int, **data) -> None:
        self.run_async(update_book, lambda _r: self.load(), id_, **data)

    def remove_book(self, id_: int) -> None:
        self.run_async(delete_book, lambda _r: self.load(), id_)

    def add_course(self, **data) -> None:
        self.run_async(add_course, lambda _r: self.load(), **data)

    def update_course(self, id_: int, **data) -> None:
        self.run_async(update_course, lambda _r: self.load(), id_, **data)

    def remove_course(self, id_: int) -> None:
        self.run_async(delete_course, lambda _r: self.load(), id_)
