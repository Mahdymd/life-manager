# Life Manager — مدیریت زندگی

برنامهٔ دسکتاپ فارسی برای مدیریت تسک، هدف، عادت، مالی، سلامت، تمرکز (پومودورو)، یادداشت، تقویم شمسی و آنالیتیکس.

نسخه: **1.0.0** (در حال توسعه) · زبان: Python · رابط: PySide6 (Qt 6) · پایگاه‌داده: SQLite

## پیش‌نیاز

- Python 3.10 یا جدیدتر
- ویندوز ۱۰/۱۱ (یا لینوکس / macOS)

## نصب و اجرا

### ویندوز

```bat
setup.bat
python main.py
```

یا دستی:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### لینوکس / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

داده‌های شخصی (دیتابیس، لاگ، بکاپ) در پوشهٔ `data/` کنار برنامه ذخیره می‌شوند و به گیت‌هاب فرستاده **نمی‌شوند**.

## میانبرهای اصلی

| کلید | کار |
|---|---|
| `Ctrl+1` … `Ctrl+9` | جابه‌جایی بین ماژول‌ها |
| `Ctrl+K` / `Ctrl+F` | پالت دستورات |
| `Ctrl+N` | مورد جدید |
| `Ctrl+Shift+N` | یادداشت سریع |
| `Ctrl+Z` | واگرد |
| `Ctrl+D` | تغییر تم |
| `Ctrl+B` | بکاپ دستی |
| `Ctrl+,` | تنظیمات |
| `F5` | تازه‌سازی |

## ساختار پروژه

```
main.py                 نقطهٔ ورود
config.py               ثابت‌ها و مسیرها
core/domain/            مدل‌ها و enumها
core/repositories/      لایهٔ دسترسی به SQLite
core/services/          منطق کسب‌وکار
core/database/          اتصال، سلامت، migration
ui/pages/               صفحات ۱۳ ماژول
ui/viewmodels/          MVVM
ui/components/          کامپوننت‌های مشترک
ui/style/               تم تیره/روشن
utils/                  تاریخ شمسی، لاگ، اعتبارسنجی
tests/                  تست‌ها (pytest)
assets/fonts|sounds     فونت وزیرمتن و صداها (اختیاری)
```

## تست

```bash
pip install pytest pytest-qt
python -m pytest -v
```

روی سیستم‌های بدون نمایشگر:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -v
```

## حریم خصوصی

این مخزن **عمومی** است. پوشهٔ `data/` در `.gitignore` است تا اطلاعات مالی، روزانه‌نویسی و تسک‌های شخصی هرگز commit نشوند. اگر قبلاً دیتابیس را جایی کپی کرده‌اید، آن را در ریپو نگذارید.
