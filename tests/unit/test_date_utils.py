"""Date helpers used by every Jalali calendar grid."""

from datetime import date
from utils.date_utils import iran_weekday, weekday_name_fa, days_in_jalali_month


def test_weekday_names_cover_full_week():
    # 19–25 Sep 2026 is Sat–Fri
    names = [weekday_name_fa(date(2026, 9, d)) for d in range(19, 26)]
    assert names == ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    assert [iran_weekday(date(2026, 9, d)) for d in range(19, 26)] == list(range(7))
