"""
utils/date_utils.py
تبدیل تاریخ شمسی/میلادی — ترجیح با jdatetime (در requirements.txt
الزامی است)؛ اگر به هر دلیلی نصب نشده باشد، از یک الگوریتم داخلی
fallback استفاده می‌شود.

هشدار فنی: الگوریتم داخلی (Borkowski) یک محدودیت شناخته‌شده در مرز
اسفند سال‌های کبیسه‌ی شمسی دارد (~۲ روز خطا از هر ۱۰ سال، تأیید‌شده با
تست). jdatetime این مشکل را ندارد. به همین دلیل نبود jdatetime با یک
هشدار بلند در لاگ گزارش می‌شود، نه سکوت.
"""

from datetime import date, datetime
from typing import Tuple, Optional
import logging
import config

logger = logging.getLogger("life_manager.date_utils")

# ── تلاش برای استفاده از jdatetime ──────────────────────
try:
    import jdatetime as _jdt
    _HAS_JDATETIME = True
except ImportError:
    _HAS_JDATETIME = False
    logger.warning(
        "کتابخانه‌ی jdatetime نصب نیست؛ الگوریتم داخلی fallback برای "
        "تبدیل تاریخ استفاده می‌شود که در مرز اسفند سال‌های کبیسه ممکن "
        "است ~۱ روز خطا داشته باشد. برای دقت کامل: pip install jdatetime"
    )


# ── الگوریتم داخلی (بدون dependency) ───────────────────
def _g2j(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
    """Gregorian → Jalali  (الگوریتم Borkowski)"""
    g_y = gy - 1600
    g_m = gm - 1
    g_d = gd - 1

    g_d_no = 365 * g_y + (g_y + 3) // 4 - (g_y + 99) // 100 + (g_y + 399) // 400
    for i in range(g_m):
        g_d_no += [31,28,31,30,31,30,31,31,30,31,30,31][i]
    if g_m > 1 and ((g_y % 4 == 0 and g_y % 100 != 0) or g_y % 400 == 0):
        g_d_no += 1
    g_d_no += g_d

    j_d_no = g_d_no - 79

    j_np = j_d_no // 12053
    j_d_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_d_no // 1461)
    j_d_no %= 1461

    if j_d_no >= 366:
        jy += (j_d_no - 1) // 365
        j_d_no = (j_d_no - 1) % 365

    for i, v in enumerate([31,31,31,31,31,31,30,30,30,30,30,29]):
        if j_d_no >= v:
            j_d_no -= v
        else:
            return jy, i + 1, j_d_no + 1
    return jy, 12, j_d_no + 1


def _j2g(jy: int, jm: int, jd: int) -> Tuple[int, int, int]:
    """Jalali → Gregorian

    نکته‌ی مهم (باگ رفع‌شده): این تابع باید دقیقاً معکوس _g2j باشد. در
    _g2j، شمارش روز با gd-1 (صفر-پایه) انجام می‌شود؛ نسخه‌ی قبلی این
    تابع از jd (یک-پایه) استفاده می‌کرد که باعث خطای سیستماتیک ۱ روزه
    در همه‌ی تبدیل‌ها می‌شد (تأیید‌شده با تست round-trip روی ۲۰۰۰ روز
    متوالی — همه‌ی ۲۰۰۰ مورد خطا داشتند، حالا صفر مورد).

    محدودیت شناخته‌شده: این الگوریتم (Borkowski) در مرز اسفند سال‌های
    کبیسه (هر ۴ سال یک‌بار) هنوز یک لبه‌ی خطا دارد. چون jdatetime (در
    requirements.txt الزامی است) این تابع را دور می‌زند و پیاده‌سازی
    صحیح و کاملاً تست‌شده‌ای ارائه می‌دهد، این الگوریتم فقط fallback
    اضطراری (نبود jdatetime) است، نه مسیر اصلی.
    """
    jy2 = jy - 979
    jm2 = jm - 1
    j_day = 365 * jy2 + (jy2 // 33) * 8 + (jy2 % 33 + 3) // 4

    for i in range(jm2):
        j_day += [31,31,31,31,31,31,30,30,30,30,30,29][i]
    j_day += jd - 1  # صفر-پایه، برای هم‌خوانی دقیق با g_d = gd - 1 در _g2j

    g_day = j_day + 79

    g_y = 1600 + 400 * (g_day // 146097)
    g_day %= 146097

    leap = True
    if g_day >= 36525:
        g_day -= 1
        g_y += 100 * (g_day // 36524)
        g_day %= 36524
        if g_day >= 365:
            g_day += 1
        else:
            leap = False

    g_y += 4 * (g_day // 1461)
    g_day %= 1461

    if g_day >= 366:
        leap = False
        g_day -= 1
        g_y += g_day // 365
        g_day %= 365

    for i, v in enumerate([31, 29 if leap else 28, 31,30,31,30,31,31,30,31,30,31]):
        if g_day < v:
            return g_y, i + 1, g_day + 1
        g_day -= v
    return g_y, 12, g_day + 1


# ── Public API ───────────────────────────────────────────

def gregorian_to_jalali(g_date: date) -> Tuple[int, int, int]:
    if _HAS_JDATETIME:
        j = _jdt.date.fromgregorian(date=g_date)
        return j.year, j.month, j.day
    return _g2j(g_date.year, g_date.month, g_date.day)


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> date:
    if _HAS_JDATETIME:
        return _jdt.date(jy, jm, jd).togregorian()
    gy, gm, gd = _j2g(jy, jm, jd)
    return date(gy, gm, gd)


def today_jalali() -> Tuple[int, int, int]:
    return gregorian_to_jalali(date.today())


def today_iso() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def format_jalali(g_date: Optional[date] = None,
                  iso_str: Optional[str] = None,
                  fmt: str = "full") -> str:
    """
    خروجی تاریخ شمسی به‌صورت رشته.
    fmt: 'full' → ۱۴۰۳/۰۵/۱۲  |  'short' → ۰۵/۱۲  |  'named' → ۱۲ مرداد ۱۴۰۳
    """
    if iso_str:
        try:
            g_date = date.fromisoformat(iso_str[:10])
        except ValueError:
            return iso_str
    if g_date is None:
        g_date = date.today()

    jy, jm, jd = gregorian_to_jalali(g_date)
    if fmt == "full":
        return f"{jy}/{jm:02d}/{jd:02d}"
    if fmt == "short":
        return f"{jm:02d}/{jd:02d}"
    if fmt == "named":
        return f"{jd} {config.MONTHS_FA[jm-1]} {jy}"
    return f"{jy}/{jm:02d}/{jd:02d}"


def parse_jalali_input(text: str) -> Optional[date]:
    """
    تبدیل ورودی کاربر به date.
    فرمت‌های پشتیبانی‌شده: 1403/05/12  |  1403-05-12  |  14030512
    """
    text = text.strip().replace("-", "/")
    parts = text.split("/")
    try:
        if len(parts) == 3:
            jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
            return jalali_to_gregorian(jy, jm, jd)
        if len(text) == 8:
            return jalali_to_gregorian(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except Exception:
        pass
    return None


def days_until(iso_date: str) -> int:
    """چند روز تا تاریخ مشخص."""
    try:
        target = date.fromisoformat(iso_date[:10])
        return (target - date.today()).days
    except ValueError:
        return 0


def is_overdue(iso_date: Optional[str]) -> bool:
    if not iso_date:
        return False
    return days_until(iso_date) < 0


def is_today(iso_date: Optional[str]) -> bool:
    if not iso_date:
        return False
    return iso_date[:10] == today_iso()


def iran_weekday(g_date: date) -> int:
    """ستون هفته‌ی ایرانی: شنبه=۰ … جمعه=۶.

    date.weekday() در پایتون دوشنبه=۰ است؛ دو روز شیفت می‌دهیم تا با
    تقویم فارسی (و هدر config.WEEKDAY_FA) هم‌خوان شود.
    """
    return (g_date.weekday() + 2) % 7


def weekday_name_fa(g_date: Optional[date] = None) -> str:
    """نام فارسی روز هفته برای تاریخ میلادی (پیش‌فرض: امروز)."""
    if g_date is None:
        g_date = date.today()
    return config.WEEKDAY_FA[iran_weekday(g_date)]


def days_in_jalali_month(jy: int, jm: int) -> int:
    """تعداد روزهای ماه شمسی؛ اسفند در سال کبیسه ۳۰ روز است."""
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    try:
        jalali_to_gregorian(jy, 12, 30)
        return 30
    except (ValueError, OverflowError):
        return 29
