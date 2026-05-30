from __future__ import annotations

from storage.db import get_connection, transaction


class DailyAssessmentRepo:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        conn = get_connection(self.db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS daily_assessments "
            "(date TEXT PRIMARY KEY, score INTEGER NOT NULL, manual INTEGER NOT NULL DEFAULT 0)"
        )
        conn.commit()

    def get(self, date: str) -> dict | None:
        conn = get_connection(self.db_path)
        row = conn.execute(
            "SELECT date, score, manual FROM daily_assessments WHERE date=?", (date,)
        ).fetchone()
        if row:
            return {"date": row["date"], "score": row["score"], "manual": row["manual"]}
        return None

    def get_range(self, start: str, end: str) -> list[dict]:
        conn = get_connection(self.db_path)
        rows = conn.execute(
            "SELECT date, score, manual FROM daily_assessments WHERE date BETWEEN ? AND ? ORDER BY date",
            (start, end),
        ).fetchall()
        return [{"date": r["date"], "score": r["score"], "manual": r["manual"]} for r in rows]

    def upsert(self, date: str, score: int, manual: int = 0) -> None:
        with transaction(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO daily_assessments (date, score, manual) VALUES (?, ?, ?)",
                (date, score, manual),
            )
