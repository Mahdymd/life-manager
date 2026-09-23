"""main.py — نقطه ورود اصلی برنامه."""

import sys
import os
import traceback
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ensure_dirs():
    import config
    for d in [config.DATA_DIR, config.LOG_DIR, config.BACKUP_DAILY_DIR,
              config.BACKUP_WEEKLY_DIR, config.BACKUP_MONTHLY_DIR,
              config.BACKUP_MANUAL_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def _seed_default_data():
    from core.database.connection import get_connection, commit
    import config
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) FROM categories").fetchone()
    if row and row[0] > 0:
        return
    from datetime import datetime
    now = datetime.now().isoformat(timespec="seconds")
    for name in config.DEFAULT_TASK_CATEGORIES:
        conn.execute("INSERT OR IGNORE INTO categories(module,name,created_at) VALUES(?,?,?)",
                     ("task", name, now))
    for name in config.DEFAULT_FINANCE_CATEGORIES:
        conn.execute("INSERT OR IGNORE INTO categories(module,name,created_at) VALUES(?,?,?)",
                     ("finance", name, now))
    for name in config.DEFAULT_GOAL_CATEGORIES:
        conn.execute("INSERT OR IGNORE INTO categories(module,name,created_at) VALUES(?,?,?)",
                     ("goal", name, now))
    defaults = {
        "theme": "dark", "language": "fa",
        "currency_symbol": "تومان",
        "pomodoro_work_min": "25", "pomodoro_short_break": "5",
        "pomodoro_long_break": "15", "pomodoro_long_after": "4",
        "backup_auto": "1", "sidebar_expanded": "0",
        "last_module": "dashboard",
    }
    for k, v in defaults.items():
        conn.execute("INSERT OR IGNORE INTO app_settings(key,value,updated_at) VALUES(?,?,?)",
                     (k, v, now))
    commit()


def main() -> int:
    # 1. Directories
    try:
        _ensure_dirs()
    except Exception as e:
        print(f"[ERROR] Cannot create directories: {e}")
        return 1

    # 2. Logging
    try:
        from utils.logger import setup_logger
        setup_logger()
        import logging
        logger = logging.getLogger("life_manager")
        logger.info("Life Manager starting...")
    except Exception as e:
        print(f"[WARNING] Logging setup failed: {e}")
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("life_manager")

    # 3. Database
    try:
        from core.database.health import run_startup_check
        integrity_error = run_startup_check(quick=True)
        if integrity_error:
            logger.critical("Database integrity: %s", integrity_error)
            try:
                from PySide6.QtWidgets import QApplication, QMessageBox
                _tmp_app = QApplication.instance() or QApplication(sys.argv)
                QMessageBox.critical(None, "خطای پایگاه‌داده", integrity_error)
            except Exception:
                print(f"\n[CRITICAL] {integrity_error}\n")
            # ادامه می‌دهیم (نه return) چون ممکنه دیتای موجود هنوز تا حدی
            # قابل‌استفاده باشه؛ کاربر آگاه شده و می‌تونه دستی بکاپ بازیابی کنه.

        from core.database.migrations.migration_runner import run_migrations
        run_migrations()
        _seed_default_data()
        logger.info("Database ready.")

        # Crash detection (بخش ۷.۴ / ۱۸ اسپک): اگر اجرای قبلی تمیز بسته
        # نشده، به کاربر اطلاع بده — قبل از علامت‌گذاری اجرای جاری.
        from core.services import session_service
        if not session_service.was_previous_session_clean():
            logger.warning("Previous session did not exit cleanly (possible crash).")
            try:
                from PySide6.QtWidgets import QApplication, QMessageBox
                _tmp_app = QApplication.instance() or QApplication(sys.argv)
                QMessageBox.warning(
                    None, "بازیابی جلسه",
                    "برنامه دفعه‌ی قبل به‌طور غیرمنتظره بسته شده بود.\n"
                    "پایگاه‌داده با WAL کار می‌کند و داده‌ها معمولاً سالم‌اند؛ "
                    "در صورت مشاهده‌ی هرگونه ناهماهنگی، از منوی تنظیمات "
                    "می‌توانید آخرین بکاپ خودکار را بازیابی کنید.",
                )
            except Exception:
                print("[WARNING] Previous session did not exit cleanly.")
        session_service.mark_running_now()
    except Exception as e:
        logger.critical("Database failed: %s\n%s", e, traceback.format_exc())
        print(f"\n[CRITICAL] Database error:\n{e}\n")
        print("Try deleting data/life_manager.db and restarting.")
        return 1

    # 4. Qt + Theme
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        app = QApplication(sys.argv)
        app.setApplicationName("Life Manager")
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    except ImportError:
        print("\n[ERROR] PySide6 not installed.\nRun: pip install PySide6\n")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Qt error: {e}\n")
        return 1

    # 5. Theme Manager
    try:
        from ui.style.theme_manager import ThemeManager
        theme_mgr = ThemeManager(app)
    except Exception as e:
        logger.error("ThemeManager error (continuing with no style): %s", e)
        theme_mgr = None

    # 5.5 Reduced motion preference (باید قبل از ساخت هر SkeletonLoader اعمال شود)
    try:
        from core.repositories.settings_repository import SettingsRepository
        from ui.components.skeleton_loader import set_reduced_motion
        set_reduced_motion(SettingsRepository().get_bool("reduced_motion", False))
    except Exception as e:
        logger.warning("Could not apply reduced-motion preference: %s", e)

    # 6. Main Window
    try:
        from ui.main_window import MainWindow
        window = MainWindow(theme_mgr)
        window.show()
        logger.info("Window displayed.")
    except Exception as e:
        logger.critical("Main window error: %s\n%s", e, traceback.format_exc())
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "خطای بحرانی", str(e))
        except Exception:
            print(f"\n[CRITICAL] {e}\n{traceback.format_exc()}")
        return 1

    # 7. Global exception hook
    def _uncaught(etype, evalue, etb):
        msg = "".join(traceback.format_exception(etype, evalue, etb))
        logger.critical("Uncaught exception:\n%s", msg)
        # طبق بخش ۱۹ اسپک: کاربر باید از خطای غیرمنتظره مطلع شود، نه
        # اینکه برنامه بی‌سروصدا رفتار عجیب داشته باشد. جزئیات فنی در
        # لاگ می‌ماند؛ به کاربر فقط پیام قابل‌فهم و راه‌حل نشان داده می‌شود.
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None, "خطای غیرمنتظره",
                "یک خطای غیرمنتظره رخ داد. جزئیات فنی در فایل لاگ ذخیره شد.\n\n"
                "می‌توانید از منوی تنظیمات → دیباگ، لاگ‌ها را صادر کرده و "
                "برای بررسی ارسال کنید.\n\n"
                "داده‌های شما در دیتابیس دست‌نخورده باقی مانده‌اند."
            )
        except Exception:
            pass

    sys.excepthook = _uncaught

    exit_code = app.exec()
    logger.info("Life Manager exited with code %d.", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
