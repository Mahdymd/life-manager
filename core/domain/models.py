"""core/domain/models.py — مدل‌های domain خالص بدون هیچ وابستگی به لایه دیگر."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from core.domain.enums import (
    GoalHorizon, GoalStatus, GoalProgressMode,
    TaskPriority, TaskStatus, TaskRecurrence,
    TransactionType, HabitFrequency,
    FocusSessionType, FocusSessionStatus,
    BookStatus, CourseStatus, ProjectStatus,
    EventType, HealthMetricType,
)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class Tag:
    id: int
    name: str
    color: str = "#6366f1"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class Category:
    id: int
    module: str
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    created_at: str = field(default_factory=_now)


@dataclass
class Goal:
    id: int
    title: str
    horizon: GoalHorizon
    description: Optional[str] = None
    category_id: Optional[int] = None
    parent_goal_id: Optional[int] = None
    start_date: Optional[str] = None
    target_date: Optional[str] = None
    status: GoalStatus = GoalStatus.ACTIVE
    progress_mode: GoalProgressMode = GoalProgressMode.AUTO
    manual_progress: float = 0.0
    sort_order: int = 0
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    computed_progress: float = 0.0
    category_name: Optional[str] = None


@dataclass
class GoalKeyResult:
    id: int
    goal_id: int
    title: str
    target: float
    current: float = 0.0
    unit: Optional[str] = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class Project:
    id: int
    title: str
    description: Optional[str] = None
    goal_id: Optional[int] = None
    category_id: Optional[int] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    color: str = "#6366f1"
    sort_order: int = 0
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    task_count: int = 0
    done_count: int = 0


@dataclass
class Task:
    id: int
    title: str
    description: Optional[str] = None
    project_id: Optional[int] = None
    goal_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    category_id: Optional[int] = None
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    estimated_min: Optional[int] = None
    actual_min: Optional[int] = None
    recurrence: TaskRecurrence = TaskRecurrence.NONE
    recur_config: Optional[str] = None
    completed_at: Optional[str] = None
    sort_order: int = 0
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    category_name: Optional[str] = None
    subtask_count: int = 0
    subtask_done: int = 0


@dataclass
class Habit:
    id: int
    name: str
    description: Optional[str] = None
    goal_id: Optional[int] = None
    category: Optional[str] = None
    frequency: HabitFrequency = HabitFrequency.DAILY
    target_days: Optional[str] = None
    target_count: int = 1
    color: str = "#22c55e"
    icon: str = "⭐"
    archived: bool = False
    sort_order: int = 0
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    current_streak: int = 0
    longest_streak: int = 0
    logged_today: bool = False


@dataclass
class HabitLog:
    id: int
    habit_id: int
    date: str
    count: int = 1
    note: Optional[str] = None
    created_at: str = field(default_factory=_now)


@dataclass
class Transaction:
    id: int
    type: TransactionType
    amount: float
    date: str
    category_id: Optional[int] = None
    note: Optional[str] = None
    goal_id: Optional[int] = None
    is_recurring: bool = False
    recur_config: Optional[str] = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    category_name: Optional[str] = None


@dataclass
class Budget:
    id: int
    category_id: int
    monthly_limit: float
    alert_at_pct: int = 85
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    category_name: Optional[str] = None
    spent: float = 0.0


@dataclass
class SavingGoal:
    id: int
    title: str
    target_amount: float
    current_amount: float = 0.0
    target_date: Optional[str] = None
    goal_id: Optional[int] = None
    status: str = "active"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class JournalEntry:
    id: int
    date: str
    content: Optional[str] = None
    mood: Optional[int] = None
    energy: Optional[int] = None
    gratitude: Optional[str] = None
    wins: Optional[str] = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class Note:
    id: int
    title: str
    content: Optional[str] = None
    parent_id: Optional[int] = None
    is_pinned: bool = False
    sort_order: int = 0
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    child_count: int = 0


@dataclass
class FocusSession:
    id: int
    type: FocusSessionType
    planned_min: int
    started_at: str
    task_id: Optional[int] = None
    actual_min: Optional[int] = None
    status: FocusSessionStatus = FocusSessionStatus.COMPLETED
    ended_at: Optional[str] = None
    note: Optional[str] = None
    created_at: str = field(default_factory=_now)


@dataclass
class HealthMetric:
    id: int
    date: str
    type: HealthMetricType
    value: float
    note: Optional[str] = None
    created_at: str = field(default_factory=_now)


@dataclass
class Workout:
    id: int
    date: str
    type: str
    duration_min: Optional[int] = None
    calories: Optional[int] = None
    note: Optional[str] = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class Book:
    id: int
    title: str
    author: Optional[str] = None
    category: Optional[str] = None
    status: BookStatus = BookStatus.WANT
    total_pages: Optional[int] = None
    current_page: int = 0
    rating: Optional[int] = None
    notes: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    goal_id: Optional[int] = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class Course:
    id: int
    title: str
    platform: Optional[str] = None
    category: Optional[str] = None
    status: CourseStatus = CourseStatus.WANT
    total_lessons: Optional[int] = None
    done_lessons: int = 0
    rating: Optional[int] = None
    notes: Optional[str] = None
    goal_id: Optional[int] = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class Skill:
    id: int
    name: str
    category: Optional[str] = None
    level: int = 1
    target_level: int = 5
    note: Optional[str] = None
    goal_id: Optional[int] = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class CalendarEvent:
    id: int
    title: str
    date: str
    description: Optional[str] = None
    time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    is_all_day: bool = True
    type: EventType = EventType.PERSONAL
    recurrence: str = "none"
    recur_config: Optional[str] = None
    color: str = "#6366f1"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class AppSetting:
    key: str
    value: str
    updated_at: str = field(default_factory=_now)
