from __future__ import annotations

import json
from typing import Iterable

from core.models.task import TaskRecord
from storage.db import get_connection, transaction

_COLUMNS = "id, name, date, end_date, description, completed, repeat_days, repeat_mode, completed_dates, remind_time"
_INSERT_COLS = "name, date, end_date, description, completed, repeat_days, repeat_mode, completed_dates, remind_time"


class TaskRepository:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path

    def list_tasks(self) -> list[TaskRecord]:
        conn = get_connection(self.db_path)
        cursor = conn.execute(
            f"SELECT {_COLUMNS} FROM tasks ORDER BY date DESC, id DESC"
        )
        return [TaskRecord.from_row(row) for row in cursor.fetchall()]

    def get_task(self, task_id: int) -> TaskRecord | None:
        conn = get_connection(self.db_path)
        cursor = conn.execute(
            f"SELECT {_COLUMNS} FROM tasks WHERE id=?",
            (task_id,),
        )
        row = cursor.fetchone()
        return TaskRecord.from_row(row) if row else None

    def find_tasks(self, keyword: str) -> list[TaskRecord]:
        keyword = keyword.strip()
        if not keyword:
            return []

        like = f"%{keyword}%"
        conn = get_connection(self.db_path)
        cursor = conn.execute(
            f"""
			SELECT {_COLUMNS}
			FROM tasks
			WHERE name LIKE ? OR description LIKE ?
			ORDER BY date DESC, id DESC
			""",
            (like, like),
        )
        return [TaskRecord.from_row(row) for row in cursor.fetchall()]

    def create_task(self, task: TaskRecord) -> TaskRecord:
        with transaction(self.db_path) as conn:
            cursor = conn.execute(
                f"INSERT INTO tasks ({_INSERT_COLS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                task.to_db_values(),
            )
            task.id = int(cursor.lastrowid)
            return task

    def update_task(self, task: TaskRecord) -> TaskRecord:
        if task.id is None:
            raise ValueError("Task id is required for update")

        with transaction(self.db_path) as conn:
            conn.execute(
                f"UPDATE tasks SET name=?, date=?, end_date=?, description=?, completed=?, repeat_days=?, repeat_mode=?, completed_dates=?, remind_time=? WHERE id=?",
                (*task.to_db_values(), task.id),
            )
            return task

    def delete_task(self, task_id: int) -> None:
        with transaction(self.db_path) as conn:
            conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def bulk_delete(self, task_ids: Iterable[int]) -> None:
        ids = list(task_ids)
        if not ids:
            return

        placeholders = ",".join(["?"] * len(ids))
        with transaction(self.db_path) as conn:
            conn.execute(
                f"DELETE FROM tasks WHERE id IN ({placeholders})",
                ids,
            )

    def delete_all(self) -> None:
        with transaction(self.db_path) as conn:
            conn.execute("DELETE FROM tasks")

    def create_many(self, tasks: Iterable[TaskRecord]) -> list[TaskRecord]:
        created: list[TaskRecord] = []
        with transaction(self.db_path) as conn:
            for task in tasks:
                cursor = conn.execute(
                    f"INSERT INTO tasks ({_INSERT_COLS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    task.to_db_values(),
                )
                task.id = int(cursor.lastrowid)
                created.append(task)
        return created
