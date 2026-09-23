"""config.py — ثابت‌های سراسری برنامه (تنها منبع حقیقت)."""

from pathlib import Path

# ── مسیرها ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DB_PATH  = DATA_DIR / "life_manager.db"
LOG_DIR  = DATA_DIR / "logs"
LOG_PATH = LOG_DIR / "app.log"

BACKUP_DIR         = DATA_DIR / "backups"
BACKUP_DAILY_DIR   = BACKUP_DIR / "daily"
BACKUP_WEEKLY_DIR  = BACKUP_DIR / "weekly"
BACKUP_MONTHLY_DIR = BACKUP_DIR / "monthly"
BACKUP_MANUAL_DIR  = BACKUP_DIR / "manual"

ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR  = ASSETS_DIR / "fonts"
SOUNDS_DIR = ASSETS_DIR / "sounds"

# ── اطلاعات برنامه ───────────────────────────────────────
APP_NAME        = "Life Manager"
APP_NAME_FA     = "مدیریت زندگی"
APP_VERSION     = "1.0.0"
APP_DESCRIPTION = "سیستم جامع مدیریت زندگی"
SCHEMA_VERSION  = 3  # aligned with highest migration (v003)

# ── دیتابیس ─────────────────────────────────────────────
DB_TIMEOUT       = 30
DB_BUSY_TIMEOUT  = 5000

# ── بکاپ ────────────────────────────────────────────────
BACKUP_KEEP_DAILY   = 30
BACKUP_KEEP_WEEKLY  = 12
BACKUP_KEEP_MONTHLY = 12

# ── لاگ ─────────────────────────────────────────────────
LOG_MAX_BYTES    = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 4

# ── UI ──────────────────────────────────────────────────
WINDOW_MIN_WIDTH      = 1100
WINDOW_MIN_HEIGHT     = 700
WINDOW_DEFAULT_WIDTH  = 1400
WINDOW_DEFAULT_HEIGHT = 860
SIDEBAR_WIDTH         = 72
SIDEBAR_EXPANDED      = 224
ANIMATION_DURATION    = 200

# ── Pomodoro ─────────────────────────────────────────────
POMODORO_WORK_MIN    = 25
POMODORO_SHORT_BREAK = 5
POMODORO_LONG_BREAK  = 15
POMODORO_LONG_AFTER  = 4

# ── برچسب‌ها (رنگ‌ها فقط از ThemeManager) ────────────────
HORIZON_LABELS = {"vision": "چشم‌انداز", "annual": "سالانه", "quarterly": "فصلی"}
PRIORITY_LABELS  = {"urgent": "فوری", "high": "بالا", "medium": "متوسط", "low": "پایین"}

STATUS_LABELS_TASK = {
    "todo": "انجام‌نشده", "in_progress": "در حال انجام",
    "done": "انجام‌شده",  "cancelled": "لغوشده",
}
STATUS_LABELS_GOAL = {
    "active": "فعال", "done": "انجام‌شده",
    "paused": "متوقف", "cancelled": "لغوشده",
}

# هفته‌ی ایرانی از شنبه شروع می‌شود (نه دوشنبه). این لیست هدر تقویم است؛
# برای نگاشت date.weekday() از utils.date_utils.iran_weekday / weekday_name_fa استفاده کنید.
WEEKDAY_FA = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
MONTHS_FA  = [
    "فروردین", "اردیبهشت", "خرداد",
    "تیر",     "مرداد",    "شهریور",
    "مهر",     "آبان",     "آذر",
    "دی",      "بهمن",     "اسفند",
]

DEFAULT_TASK_CATEGORIES    = ["برنامه‌نویسی", "باشگاه", "مطالعه", "دانشگاه", "شخصی", "کاری", "متفرقه"]
DEFAULT_FINANCE_CATEGORIES = ["غذا", "حمل‌ونقل", "تحصیل", "تفریح", "باشگاه", "حقوق", "متفرقه"]
DEFAULT_GOAL_CATEGORIES    = ["برنامه‌نویسی", "تناسب‌اندام", "مطالعه", "درآمد", "تحصیل", "رشد فردی"]


def __getattr__(name: str):
    """Lazy theme-aware colour maps — never hardcode hex here.
    Existing call sites using config.PRIORITY_COLORS / HORIZON_COLORS
    continue to work and now resolve from ThemeManager tokens.
    """
    if name == "PRIORITY_COLORS":
        from ui.style.theme_manager import priority_color
        return {k: priority_color(k) for k in ("urgent", "high", "medium", "low")}
    if name == "HORIZON_COLORS":
        from ui.style.theme_manager import horizon_color
        return {k: horizon_color(k) for k in ("vision", "annual", "quarterly")}
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
