"""core/domain/enums.py — تمام enum های domain."""

from enum import Enum


class GoalHorizon(str, Enum):
    VISION    = "vision"
    ANNUAL    = "annual"
    QUARTERLY = "quarterly"


class GoalStatus(str, Enum):
    ACTIVE    = "active"
    DONE      = "done"
    PAUSED    = "paused"
    CANCELLED = "cancelled"


class GoalProgressMode(str, Enum):
    AUTO   = "auto"
    MANUAL = "manual"


class TaskPriority(str, Enum):
    URGENT = "urgent"
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


class TaskStatus(str, Enum):
    TODO        = "todo"
    IN_PROGRESS = "in_progress"
    DONE        = "done"
    CANCELLED   = "cancelled"


class TaskRecurrence(str, Enum):
    NONE    = "none"
    DAILY   = "daily"
    WEEKLY  = "weekly"
    MONTHLY = "monthly"
    CUSTOM  = "custom"


class TransactionType(str, Enum):
    INCOME   = "income"
    EXPENSE  = "expense"
    TRANSFER = "transfer"


class HabitFrequency(str, Enum):
    DAILY  = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class FocusSessionType(str, Enum):
    POMODORO    = "pomodoro"
    SHORT_BREAK = "short_break"
    LONG_BREAK  = "long_break"
    CUSTOM      = "custom"


class FocusSessionStatus(str, Enum):
    COMPLETED   = "completed"
    INTERRUPTED = "interrupted"
    SKIPPED     = "skipped"


class BookStatus(str, Enum):
    WANT      = "want"
    READING   = "reading"
    DONE      = "done"
    ABANDONED = "abandoned"


class CourseStatus(str, Enum):
    WANT        = "want"
    IN_PROGRESS = "in_progress"
    DONE        = "done"
    ABANDONED   = "abandoned"


class ProjectStatus(str, Enum):
    ACTIVE   = "active"
    DONE     = "done"
    ARCHIVED = "archived"


class EventType(str, Enum):
    PERSONAL    = "personal"
    BIRTHDAY    = "birthday"
    ANNIVERSARY = "anniversary"
    REMINDER    = "reminder"


class HealthMetricType(str, Enum):
    WEIGHT        = "weight"
    WATER         = "water"
    SLEEP_HOURS   = "sleep_hours"
    SLEEP_QUALITY = "sleep_quality"


class Theme(str, Enum):
    DARK   = "dark"
    LIGHT  = "light"
    SYSTEM = "system"
