from __future__ import annotations

from storage.db import get_connection


class SettingRepo:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        conn = get_connection(self.db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        conn.commit()

    def get(self, key: str, default: str | None = None) -> str | None:
        conn = get_connection(self.db_path)
        row = conn.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        conn = get_connection(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
