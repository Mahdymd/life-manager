"""core/services/backup_service.py — سیستم بکاپ سه‌لایه‌ای."""

import zipfile, shutil, json, logging
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict
import config
from core.domain.exceptions import BackupError, RestoreError
from core.database.connection import close_connection, get_connection

logger = logging.getLogger("life_manager.backup")


def _backup_info() -> Dict:
    conn = get_connection()
    tables = ["tasks","goals","habits","transactions","journal_entries",
              "notes","focus_sessions","health_metrics","books","courses","events"]
    records = {}
    for t in tables:
        try:
            row = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()
            records[t] = row[0] if row else 0
        except Exception:
            records[t] = 0
    size_kb = config.DB_PATH.stat().st_size // 1024 if config.DB_PATH.exists() else 0
    return {
        "app_version": config.APP_VERSION,
        "created_at": datetime.now().isoformat(),
        "db_size_kb": size_kb,
        "records": records,
    }


def _make_zip(zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    # فیکس حیاتی (Audit #2): چون دیتابیس روی WAL mode است، تراکنش‌های
    # اخیر ممکن است هنوز فقط در فایل life_manager.db-wal باشند و به
    # فایل اصلی merge نشده باشند. اگر این‌جا مستقیم فایل اصلی را کپی
    # کنیم، بکاپ می‌تواند دیتای چند دقیقه‌ی اخیر را جا بیندازد.
    # TRUNCATE تمام محتوای WAL را به فایل اصلی منتقل و فایل -wal را
    # خالی می‌کند تا کپی زیر همیشه کامل و به‌روز باشد.
    try:
        conn = get_connection()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception as e:
        logger.warning("WAL checkpoint before backup failed (ادامه با فایل موجود): %s", e)

    info = _backup_info()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if config.DB_PATH.exists():
            zf.write(config.DB_PATH, "life_manager.db")
        zf.writestr("backup_info.json", json.dumps(info, ensure_ascii=False, indent=2))
    logger.info("Backup created: %s (%.1f KB)", zip_path.name, zip_path.stat().st_size/1024)


def _prune(directory: Path, keep: int) -> None:
    files = sorted(directory.glob("*.zip"))
    for f in files[:-keep]:
        f.unlink()
        logger.debug("Pruned old backup: %s", f.name)


def run_auto_backup() -> None:
    """اجرای بکاپ روزانه/هفتگی/ماهانه به صورت خودکار."""
    today = date.today()
    ds = today.isoformat()

    # روزانه
    daily_path = config.BACKUP_DAILY_DIR / f"backup_{ds}.zip"
    if not daily_path.exists():
        _make_zip(daily_path)
        _prune(config.BACKUP_DAILY_DIR, config.BACKUP_KEEP_DAILY)

    # هفتگی (شنبه = weekday 5)
    if today.weekday() == 5:
        week = today.isocalendar()
        weekly_path = config.BACKUP_WEEKLY_DIR / f"backup_{week.year}-W{week.week:02d}.zip"
        if not weekly_path.exists():
            _make_zip(weekly_path)
            _prune(config.BACKUP_WEEKLY_DIR, config.BACKUP_KEEP_WEEKLY)

    # ماهانه (اول ماه)
    if today.day == 1:
        monthly_path = config.BACKUP_MONTHLY_DIR / f"backup_{ds[:7]}.zip"
        if not monthly_path.exists():
            _make_zip(monthly_path)
            _prune(config.BACKUP_MONTHLY_DIR, config.BACKUP_KEEP_MONTHLY)


def manual_backup() -> Path:
    """بکاپ دستی با timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = config.BACKUP_MANUAL_DIR / f"backup_manual_{ts}.zip"
    _make_zip(path)
    return path


def restore_backup(zip_path: Path) -> None:
    """بازیابی از فایل بکاپ."""
    if not zip_path.exists():
        raise RestoreError(f"فایل بکاپ پیدا نشد: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            if "life_manager.db" not in names:
                raise RestoreError("فایل بکاپ معتبر نیست.")
            close_connection()
            tmp = config.DATA_DIR / "life_manager_restore_tmp.db"
            with zf.open("life_manager.db") as src, open(tmp, "wb") as dst:
                shutil.copyfileobj(src, dst)
            backup_current = config.DATA_DIR / f"life_manager_before_restore_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
            if config.DB_PATH.exists():
                shutil.copy2(config.DB_PATH, backup_current)
            shutil.move(str(tmp), str(config.DB_PATH))
            # فایل‌های -wal/-shm باقی‌مانده متعلق به دیتابیس قبلی هستند؛
            # اگر پاک نشوند، هنگام باز شدن دوباره‌ی فایل جدید با آن‌ها
            # ترکیب می‌شوند و می‌توانند دیتا را ناسازگار/خراب کنند.
            for suffix in ("-wal", "-shm"):
                stale = Path(str(config.DB_PATH) + suffix)
                if stale.exists():
                    stale.unlink()
        logger.info("Restore completed from: %s", zip_path.name)
    except RestoreError:
        raise
    except Exception as e:
        raise RestoreError(str(e)) from e


def list_backups() -> List[Dict]:
    result = []
    for subdir, label in [
        (config.BACKUP_DAILY_DIR, "روزانه"),
        (config.BACKUP_WEEKLY_DIR, "هفتگی"),
        (config.BACKUP_MONTHLY_DIR, "ماهانه"),
        (config.BACKUP_MANUAL_DIR, "دستی"),
    ]:
        for f in sorted(subdir.glob("*.zip"), reverse=True):
            try:
                with zipfile.ZipFile(f, "r") as zf:
                    if "backup_info.json" in zf.namelist():
                        info = json.loads(zf.read("backup_info.json"))
                    else:
                        info = {}
            except Exception:
                info = {}
            result.append({
                "path": f,
                "name": f.name,
                "type": label,
                "size_kb": f.stat().st_size // 1024,
                "created_at": info.get("created_at",""),
                "records": info.get("records", {}),
            })
    return result


_STATS_TABLES = (
    "tasks", "goals", "habits", "transactions", "journal_entries", "notes",
    "focus_sessions", "health_metrics", "books", "courses", "events",
)

_RESET_TABLES = (
    "tasks", "goals", "habit_logs", "habits", "transactions", "journal_entries",
    "notes", "focus_sessions", "health_metrics", "workouts", "books", "courses",
    "skills", "events", "saving_goals", "budgets",
)


def get_db_stats_text() -> str:
    """Human-readable per-table record counts for Settings UI."""
    conn = get_connection()
    lines = []
    for t in _STATS_TABLES:
        try:
            row = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()
            count = row[0] if row else 0
            if count > 0:
                lines.append(f"• {t}: {count} رکورد")
        except Exception:
            continue
    size_kb = config.DB_PATH.stat().st_size // 1024 if config.DB_PATH.exists() else 0
    lines.append(f"\nحجم پایگاه داده: {size_kb} KB")
    return "\n".join(lines) if lines else "هیچ داده‌ای ثبت نشده است."


def reset_all_user_data() -> None:
    """Destructive: backup first, then DELETE all user tables.
    Table names are a fixed allow-list (never user-supplied).
    """
    manual_backup()
    from core.database.connection import commit
    conn = get_connection()
    for t in _RESET_TABLES:
        try:
            conn.execute(f"DELETE FROM {t}")
        except Exception as e:
            logger.warning("reset skip %s: %s", t, e)
    commit()
    logger.info("All user data reset after safety backup.")
