"""core/repositories/learning_repository.py"""

from typing import List, Dict
from core.repositories.base_repository import BaseRepository
from core.domain.models import Book, Course, Skill
from core.domain.enums import BookStatus, CourseStatus


class LearningRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("books")

    # ── Books ──
    def get_books(self, status: str = None) -> List[Book]:
        if status:
            rows = self._fetch_all(
                "SELECT * FROM books WHERE status=? ORDER BY updated_at DESC", (status,))
        else:
            rows = self._fetch_all("SELECT * FROM books ORDER BY updated_at DESC")
        return [self._to_book(r) for r in rows]

    def _to_book(self, row) -> Book:
        d = self._row_to_dict(row)
        return Book(
            id=d["id"], title=d["title"], author=d.get("author"),
            category=d.get("category"), status=BookStatus(d.get("status","want")),
            total_pages=d.get("total_pages"), current_page=d.get("current_page",0),
            rating=d.get("rating"), notes=d.get("notes"),
            started_at=d.get("started_at"), finished_at=d.get("finished_at"),
            goal_id=d.get("goal_id"),
            created_at=d["created_at"], updated_at=d["updated_at"],
        )

    def add_book(self, title: str, **kwargs) -> Book:
        id_ = self._conn().execute("""
            INSERT INTO books(title,author,category,status,total_pages,goal_id,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (title, kwargs.get("author"), kwargs.get("category"), kwargs.get("status","want"),
             kwargs.get("total_pages"), kwargs.get("goal_id"), self._now(), self._now())).lastrowid
        from core.database.connection import commit
        commit()
        return self._to_book(self._fetch_one("SELECT * FROM books WHERE id=?", (id_,)))

    def update_book(self, id_: int, **kwargs) -> bool:
        sets = ", ".join(f"{k}=?" for k in kwargs)
        self._conn().execute(f"UPDATE books SET {sets},updated_at=? WHERE id=?",
                             (*kwargs.values(), self._now(), id_))
        from core.database.connection import commit
        commit()
        return True

    # ── Courses ──
    def get_courses(self, status: str = None) -> List[Course]:
        if status:
            rows = self._fetch_all(
                "SELECT * FROM courses WHERE status=? ORDER BY updated_at DESC", (status,))
        else:
            rows = self._fetch_all("SELECT * FROM courses ORDER BY updated_at DESC")
        return [self._to_course(r) for r in rows]

    def _to_course(self, row) -> Course:
        d = self._row_to_dict(row)
        return Course(
            id=d["id"], title=d["title"], platform=d.get("platform"),
            category=d.get("category"), status=CourseStatus(d.get("status","want")),
            total_lessons=d.get("total_lessons"), done_lessons=d.get("done_lessons",0),
            rating=d.get("rating"), notes=d.get("notes"), goal_id=d.get("goal_id"),
            created_at=d["created_at"], updated_at=d["updated_at"],
        )

    def add_course(self, title: str, **kwargs) -> Course:
        id_ = self._conn().execute("""
            INSERT INTO courses(title,platform,category,status,total_lessons,goal_id,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (title, kwargs.get("platform"), kwargs.get("category"),
             kwargs.get("status","want"), kwargs.get("total_lessons"),
             kwargs.get("goal_id"), self._now(), self._now())).lastrowid
        from core.database.connection import commit
        commit()
        return self._to_course(self._fetch_one("SELECT * FROM courses WHERE id=?", (id_,)))

    def update_course(self, id_: int, **kwargs) -> bool:
        sets = ", ".join(f"{k}=?" for k in kwargs)
        self._conn().execute(f"UPDATE courses SET {sets},updated_at=? WHERE id=?",
                             (*kwargs.values(), self._now(), id_))
        from core.database.connection import commit
        commit()
        return True

    # ── Skills ──
    def get_skills(self) -> List[Skill]:
        rows = self._fetch_all("SELECT * FROM skills ORDER BY category,name")
        result = []
        for r in rows:
            d = self._row_to_dict(r)
            result.append(Skill(
                id=d["id"], name=d["name"], category=d.get("category"),
                level=d.get("level", 1), target_level=d.get("target_level", 5),
                note=d.get("note"), goal_id=d.get("goal_id"),
                created_at=d["created_at"], updated_at=d["updated_at"],
            ))
        return result

    def upsert_skill(self, name: str, **kwargs) -> None:
        now = self._now()
        self._conn().execute("""
            INSERT INTO skills(name,category,level,target_level,note,goal_id,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (name, kwargs.get("category"), kwargs.get("level",1),
             kwargs.get("target_level",5), kwargs.get("note"),
             kwargs.get("goal_id"), now, now))
        from core.database.connection import commit
        commit()

    def get_stats(self) -> Dict:
        b = self._fetch_one("""
            SELECT COUNT(*) AS total,
              SUM(status='reading') AS reading,
              SUM(status='done') AS done
            FROM books""")
        c = self._fetch_one("""
            SELECT COUNT(*) AS total,
              SUM(status='in_progress') AS in_progress,
              SUM(status='done') AS done
            FROM courses""")
        return {"books": dict(b) if b else {}, "courses": dict(c) if c else {}}
