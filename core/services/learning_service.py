"""core/services/learning_service.py"""

from typing import List, Optional
from core.repositories.learning_repository import LearningRepository
from core.domain.models import Book, Course, Skill
from utils.validator import require

_repo = LearningRepository()


def add_book(title: str, **kwargs) -> Book:
    return _repo.add_book(require(title, "عنوان کتاب"), **kwargs)


def update_book(id_: int, **kwargs) -> bool:
    return _repo.update_book(id_, **kwargs)


def delete_book(id_: int) -> bool:
    from core.database.connection import get_connection, commit
    get_connection().execute("DELETE FROM books WHERE id=?", (id_,))
    commit()
    return True


def get_books(status: str = None) -> List[Book]:
    return _repo.get_books(status)


def add_course(title: str, **kwargs) -> Course:
    return _repo.add_course(require(title, "عنوان دوره"), **kwargs)


def update_course(id_: int, **kwargs) -> bool:
    return _repo.update_course(id_, **kwargs)


def delete_course(id_: int) -> bool:
    from core.database.connection import get_connection, commit
    get_connection().execute("DELETE FROM courses WHERE id=?", (id_,))
    commit()
    return True


def get_courses(status: str = None) -> List[Course]:
    return _repo.get_courses(status)


def get_skills() -> List[Skill]:
    return _repo.get_skills()


def add_skill(name: str, **kwargs) -> None:
    _repo.upsert_skill(require(name, "نام مهارت"), **kwargs)


def get_learning_stats() -> dict:
    return _repo.get_stats()
