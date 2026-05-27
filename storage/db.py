from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "tasks.db"

_connection_cache: dict[str, sqlite3.Connection] = {}


def resolve_db_path(db_path: str | Path | None = None) -> Path:
    if db_path is None:
        return DEFAULT_DB_PATH
    return Path(db_path)


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
		CREATE TABLE IF NOT EXISTS tasks (
			id INTEGER PRIMARY KEY,
			name TEXT NOT NULL,
			date TEXT NOT NULL,
			completed INTEGER NOT NULL DEFAULT 0
		)
		"""
    )
    # 迁移：添加 end_date 列（持续时间）
    cursor = connection.execute("PRAGMA table_info(tasks)")
    columns = {row[1] for row in cursor.fetchall()}
    if "end_date" not in columns:
        connection.execute("ALTER TABLE tasks ADD COLUMN end_date TEXT")
    if "description" not in columns:
        connection.execute("ALTER TABLE tasks ADD COLUMN description TEXT DEFAULT ''")
    connection.commit()


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = resolve_db_path(db_path)
    key = str(path)
    cached = _connection_cache.get(key)
    if cached is not None:
        try:
            cached.execute("SELECT 1")
            return cached
        except sqlite3.ProgrammingError:
            _connection_cache.pop(key, None)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    ensure_schema(connection)
    _connection_cache[key] = connection
    return connection


@contextmanager
def transaction(db_path: str | Path | None = None):
    connection = get_connection(db_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def close_all() -> None:
    for conn in _connection_cache.values():
        try:
            conn.close()
        except Exception:
            pass
    _connection_cache.clear()
