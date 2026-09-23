"""core/repositories/settings_repository.py"""

from typing import Dict, Optional
from core.database.connection import get_connection, commit


_DEFAULTS = {
    "theme": "dark",
    "language": "fa",
    "pomodoro_work_min": "25",
    "pomodoro_short_break": "5",
    "pomodoro_long_break": "15",
    "pomodoro_long_after": "4",
    "backup_auto": "1",
    "currency_symbol": "تومان",
    "sidebar_expanded": "0",
    "window_geometry": "",
    "last_module": "dashboard",
}


class SettingsRepository:
    def get(self, key: str, default: str = None) -> Optional[str]:
        conn = get_connection()
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
        if row:
            return row["value"]
        return _DEFAULTS.get(key, default)

    def set(self, key: str, value: str) -> None:
        from datetime import datetime
        now = datetime.now().isoformat(timespec="seconds")
        get_connection().execute("""
            INSERT INTO app_settings(key,value,updated_at) VALUES(?,?,?)
            ON CONFLICT(key) DO UPDATE SET value=?,updated_at=?""",
            (key, value, now, value, now))
        commit()

    def get_all(self) -> Dict[str, str]:
        defaults = dict(_DEFAULTS)
        rows = get_connection().execute("SELECT key,value FROM app_settings").fetchall()
        for r in rows:
            defaults[r["key"]] = r["value"]
        return defaults

    def get_int(self, key: str, default: int = 0) -> int:
        v = self.get(key)
        try:
            return int(v) if v is not None else default
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        v = self.get(key)
        if v is None:
            return default
        return v in ("1", "true", "True", "yes")
