from __future__ import annotations

from typing import Iterable

from core.models.task import TaskRecord
from storage.db import get_connection


class TaskRepository:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path

    def list_tasks(self) -> list[TaskRecord]:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                "SELECT id, name, date, completed FROM tasks ORDER BY date DESC, id DESC"
            )
            return [TaskRecord.from_row(row) for row in cursor.fetchall()]

    def get_task(self, task_id: int) -> TaskRecord | None:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                "SELECT id, name, date, completed FROM tasks WHERE id=?",
                (task_id,),
            )
            row = cursor.fetchone()
            return TaskRecord.from_row(row) if row else None

    def find_tasks(self, keyword: str) -> list[TaskRecord]:
        keyword = keyword.strip()
        if not keyword:
            return []

        like = f"%{keyword}%"
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
				SELECT id, name, date, completed
				FROM tasks
				WHERE name LIKE ?
				ORDER BY date DESC, id DESC
				""",
                (like,),
            )
            return [TaskRecord.from_row(row) for row in cursor.fetchall()]

    def create_task(self, task: TaskRecord) -> TaskRecord:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (name, date, completed) VALUES (?, ?, ?)",
                task.to_db_values(),
            )
            connection.commit()
            task.id = int(cursor.lastrowid)
            return task

    def update_task(self, task: TaskRecord) -> TaskRecord:
        if task.id is None:
            raise ValueError("Task id is required for update")

        with get_connection(self.db_path) as connection:
            connection.execute(
                "UPDATE tasks SET name=?, date=?, completed=? WHERE id=?",
                (*task.to_db_values(), task.id),
            )
            connection.commit()
            return task

    def delete_task(self, task_id: int) -> None:
        with get_connection(self.db_path) as connection:
            connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            connection.commit()

    def bulk_delete(self, task_ids: Iterable[int]) -> None:
        ids = list(task_ids)
        if not ids:
            return

        placeholders = ",".join(["?"] * len(ids))
        with get_connection(self.db_path) as connection:
            connection.execute(
                f"DELETE FROM tasks WHERE id IN ({placeholders})",
                ids,
            )
            connection.commit()

    def delete_all(self) -> None:
        with get_connection(self.db_path) as connection:
            connection.execute("DELETE FROM tasks")
            connection.commit()

    def create_many(self, tasks: Iterable[TaskRecord]) -> list[TaskRecord]:
        created: list[TaskRecord] = []
        with get_connection(self.db_path) as connection:
            for task in tasks:
                cursor = connection.execute(
                    "INSERT INTO tasks (name, date, completed) VALUES (?, ?, ?)",
                    task.to_db_values(),
                )
                task.id = int(cursor.lastrowid)
                created.append(task)
            connection.commit()
        return created
