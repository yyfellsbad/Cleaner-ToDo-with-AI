from __future__ import annotations

from datetime import date, datetime, timedelta

from core.models.task import TaskRecord
from storage.task_repo import TaskRepository


class TaskService:
    def __init__(self, repository: TaskRepository | None = None):
        self.repository = repository or TaskRepository()

    def list_tasks(
        self, status: str = "all", keyword: str | None = None
    ) -> list[TaskRecord]:
        tasks = self.repository.list_tasks()
        if keyword:
            normalized = keyword.strip().lower()
            if normalized:
                tasks = [task for task in tasks if normalized in task.name.lower()]

        status = status.lower()
        if status == "active":
            return [task for task in tasks if not task.completed]
        if status == "completed":
            return [task for task in tasks if task.completed]
        return tasks

    def search_tasks(self, keyword: str) -> list[TaskRecord]:
        return self.repository.find_tasks(keyword)

    def get_task(self, task_id: int) -> TaskRecord | None:
        return self.repository.get_task(task_id)

    def create_task(
        self,
        name: str,
        task_date: date | None = None,
        completed: bool = False,
    ) -> TaskRecord:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Task name cannot be empty")

        record = TaskRecord(
            name=normalized_name,
            date=task_date or date.today(),
            completed=completed,
        )
        return self.repository.create_task(record)

    def create_tasks(
        self,
        base_name: str,
        count: int,
        task_date: date | None = None,
    ) -> list[TaskRecord]:
        normalized_name = base_name.strip()
        if not normalized_name:
            raise ValueError("Task name cannot be empty")

        normalized_count = max(1, int(count))
        if normalized_count == 1:
            return [self.create_task(normalized_name, task_date)]

        tasks = [
            TaskRecord(
                name=f"{normalized_name} #{index}", date=task_date or date.today()
            )
            for index in range(1, normalized_count + 1)
        ]
        return self.repository.create_many(tasks)

    def update_task(
        self,
        task_id: int,
        name: str | None = None,
        task_date: date | None = None,
        completed: bool | None = None,
    ) -> TaskRecord:
        task = self.repository.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        if name is not None:
            task.name = name.strip() or task.name
        if task_date is not None:
            task.date = task_date
        if completed is not None:
            task.completed = completed
        return self.repository.update_task(task)

    def delete_task(self, task_id: int) -> None:
        self.repository.delete_task(task_id)

    def delete_tasks(self, task_ids: list[int]) -> list[TaskRecord]:
        existing = [
            task
            for task_id in task_ids
            if (task := self.repository.get_task(task_id)) is not None
        ]
        self.repository.bulk_delete(task_ids)
        return existing

    def delete_all_tasks(self, status: str = "all") -> list[TaskRecord]:
        existing = self.list_tasks(status=status)
        self.repository.bulk_delete(
            [task.id for task in existing if task.id is not None]
        )
        return existing

    def replace_all_tasks(self, tasks: list[TaskRecord]) -> list[TaskRecord]:
        self.repository.delete_all()
        clones = [
            TaskRecord(name=task.name, date=task.date, completed=task.completed)
            for task in tasks
        ]
        return self.repository.create_many(clones)

    def mark_complete(self, task_id: int, completed: bool = True) -> TaskRecord:
        return self.update_task(task_id, completed=completed)

    def complete_task(self, task_id: int) -> TaskRecord:
        return self.mark_complete(task_id, True)

    def uncomplete_task(self, task_id: int) -> TaskRecord:
        return self.mark_complete(task_id, False)

    def resolve_date(self, value: str | None) -> date:
        if not value:
            return date.today()

        normalized = value.strip().lower()
        today = date.today()
        if normalized in {"今天", "today"}:
            return today
        if normalized in {"明天", "tomorrow"}:
            return today + timedelta(days=1)
        if normalized in {"后天", "the day after tomorrow"}:
            return today + timedelta(days=2)

        for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d", "%m-%d"):
            try:
                parsed = datetime.strptime(value.strip(), pattern).date()
                if pattern in {"%m/%d", "%m-%d"}:
                    return parsed.replace(year=today.year)
                return parsed
            except ValueError:
                continue

        return today
