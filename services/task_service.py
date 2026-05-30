from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from core.models.task import TaskRecord
from storage.task_repo import TaskRepository


def _try_parse_time(value: str) -> tuple[int, int] | None:
    """解析 '14:30'、'9:00'、'1430' 等时间格式，返回 (hour, minute)。"""
    value = value.strip()
    # HH:MM 或 H:MM
    m = re.match(r"^(\d{1,2}):(\d{2})$", value)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return h, mi
    # HHMM
    if value.isdigit() and len(value) == 4:
        h, mi = int(value[:2]), int(value[2:])
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return h, mi
    return None


def _extract_time(text: str) -> tuple[str, tuple[int, int] | None]:
    """从文本中提取时间部分，返回 (剩余文本, (hour, minute) | None)。"""
    # 匹配 "14:30"、"9:00" 等
    m = re.search(r"(\d{1,2}:\d{2})", text)
    if m:
        time_part = _try_parse_time(m.group(1))
        if time_part:
            remaining = text[:m.start()] + text[m.end():]
            return remaining.strip(), time_part
    return text, None


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
        if status == "ongoing":
            now = datetime.now()
            return [
                task
                for task in tasks
                if task.end_date and not task.completed and task.date <= now <= task.end_date
            ]
        return tasks

    def search_tasks(self, keyword: str) -> list[TaskRecord]:
        return self.repository.find_tasks(keyword)

    def get_task(self, task_id: int) -> TaskRecord | None:
        return self.repository.get_task(task_id)

    def create_task(
        self,
        name: str,
        task_date: datetime | None = None,
        completed: bool = False,
        end_date: datetime | None = None,
        description: str = "",
        repeat_days: int = 0,
        repeat_mode: str = "once",
    ) -> TaskRecord:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Task name cannot be empty")

        record = TaskRecord(
            name=normalized_name,
            date=task_date or datetime.now().replace(second=0, microsecond=0),
            end_date=end_date,
            description=description.strip(),
            completed=completed,
            repeat_days=repeat_days,
            repeat_mode=repeat_mode,
        )
        return self.repository.create_task(record)

    def create_tasks(
        self,
        base_name: str,
        count: int,
        task_date: datetime | None = None,
        end_date: datetime | None = None,
        description: str = "",
        repeat_days: int = 0,
        repeat_mode: str = "once",
    ) -> list[TaskRecord]:
        normalized_name = base_name.strip()
        if not normalized_name:
            raise ValueError("Task name cannot be empty")

        normalized_count = max(1, int(count))
        if normalized_count == 1:
            return [self.create_task(normalized_name, task_date, end_date=end_date, description=description,
                                     repeat_days=repeat_days, repeat_mode=repeat_mode)]

        tasks = [
            TaskRecord(
                name=f"{normalized_name} #{index}",
                date=task_date or datetime.now().replace(second=0, microsecond=0),
                end_date=end_date,
                description=description,
                repeat_days=repeat_days,
                repeat_mode=repeat_mode,
            )
            for index in range(1, normalized_count + 1)
        ]
        return self.repository.create_many(tasks)

    def update_task(
        self,
        task_id: int,
        name: str | None = None,
        task_date: datetime | None = None,
        end_date: datetime | None = None,
        clear_end_date: bool = False,
        description: str | None = None,
        completed: bool | None = None,
        repeat_days: int | None = None,
        repeat_mode: str | None = None,
    ) -> TaskRecord:
        task = self.repository.get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        if name is not None:
            task.name = name.strip() or task.name
        if task_date is not None:
            task.date = task_date
        if clear_end_date:
            task.end_date = None
        elif end_date is not None:
            task.end_date = end_date
        if description is not None:
            task.description = description.strip()
        if completed is not None:
            task.completed = completed
        if repeat_days is not None:
            task.repeat_days = repeat_days
        if repeat_mode is not None:
            task.repeat_mode = repeat_mode
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
            TaskRecord(
                name=task.name,
                date=task.date,
                end_date=task.end_date,
                description=task.description,
                completed=task.completed,
                repeat_days=task.repeat_days,
                repeat_mode=task.repeat_mode,
                completed_dates=list(task.completed_dates),
            )
            for task in tasks
        ]
        return self.repository.create_many(clones)

    def mark_complete(self, task_id: int, completed: bool = True) -> TaskRecord:
        return self.update_task(task_id, completed=completed)

    def complete_task(self, task_id: int) -> TaskRecord:
        return self.mark_complete(task_id, True)

    def uncomplete_task(self, task_id: int) -> TaskRecord:
        return self.mark_complete(task_id, False)

    def resolve_date(self, value: str | None) -> datetime:
        """解析日期+时间字符串，无法识别时返回今天 00:00。"""
        if not value:
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        normalized = value.strip().lower()
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 提取时间部分
        remaining, time_part = _extract_time(value.strip())

        # 关键词匹配（使用剩余文本）
        norm2 = remaining.lower()
        if norm2 in {"今天", "today", ""} and time_part:
            return today.replace(hour=time_part[0], minute=time_part[1])
        if norm2 in {"今天", "today"}:
            return today
        if norm2 in {"明天", "tomorrow"}:
            d = today + timedelta(days=1)
            return d.replace(hour=time_part[0], minute=time_part[1]) if time_part else d
        if norm2 in {"后天", "the day after tomorrow"}:
            d = today + timedelta(days=2)
            return d.replace(hour=time_part[0], minute=time_part[1]) if time_part else d

        # 日期格式匹配
        for pattern in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                parsed = datetime.strptime(remaining, pattern)
                if time_part:
                    parsed = parsed.replace(hour=time_part[0], minute=time_part[1])
                return parsed
            except ValueError:
                continue

        # 无年份格式：手动解析
        for sep in ("/", "-"):
            parts = remaining.split(sep)
            if len(parts) == 2:
                try:
                    m, d = int(parts[0]), int(parts[1])
                    parsed = datetime(today.year, m, d)
                    if time_part:
                        parsed = parsed.replace(hour=time_part[0], minute=time_part[1])
                    return parsed
                except ValueError:
                    continue

        # 纯数字日期
        digits = remaining.strip()
        if digits.isdigit():
            month, day = None, None
            if len(digits) == 3:
                month, day = int(digits[0]), int(digits[1:])
            elif len(digits) == 4:
                month, day = int(digits[:2]), int(digits[2:])
            if month and day:
                try:
                    d = date(today.year, month, day)
                    dt = datetime(d.year, d.month, d.day)
                    if time_part:
                        dt = dt.replace(hour=time_part[0], minute=time_part[1])
                    return dt
                except ValueError:
                    pass

        return today

    @staticmethod
    def try_parse_date(value: str) -> datetime | None:
        """严格解析日期+时间字符串，失败返回 None。"""
        if not value:
            return None

        normalized = value.strip().lower()
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        remaining, time_part = _extract_time(value.strip())
        norm2 = remaining.lower()

        if norm2 in {"今天", "today", ""} and time_part:
            return today.replace(hour=time_part[0], minute=time_part[1])
        if norm2 in {"今天", "today"}:
            return today
        if norm2 in {"明天", "tomorrow"}:
            d = today + timedelta(days=1)
            return d.replace(hour=time_part[0], minute=time_part[1]) if time_part else d
        if norm2 in {"后天", "the day after tomorrow"}:
            d = today + timedelta(days=2)
            return d.replace(hour=time_part[0], minute=time_part[1]) if time_part else d

        for pattern in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                parsed = datetime.strptime(remaining, pattern)
                if time_part:
                    parsed = parsed.replace(hour=time_part[0], minute=time_part[1])
                return parsed
            except ValueError:
                continue

        for sep in ("/", "-"):
            parts = remaining.split(sep)
            if len(parts) == 2:
                try:
                    m, d = int(parts[0]), int(parts[1])
                    parsed = datetime(today.year, m, d)
                    if time_part:
                        parsed = parsed.replace(hour=time_part[0], minute=time_part[1])
                    return parsed
                except ValueError:
                    continue

        digits = remaining.strip()
        if digits.isdigit():
            month, day = None, None
            if len(digits) == 3:
                month, day = int(digits[0]), int(digits[1:])
            elif len(digits) == 4:
                month, day = int(digits[:2]), int(digits[2:])
            if month and day:
                try:
                    d = date(today.year, month, day)
                    dt = datetime(d.year, d.month, d.day)
                    if time_part:
                        dt = dt.replace(hour=time_part[0], minute=time_part[1])
                    return dt
                except ValueError:
                    pass

        return None

    @staticmethod
    def try_parse_time(value: str) -> tuple[int, int] | None:
        """解析时间字符串，返回 (hour, minute) 或 None。"""
        return _try_parse_time(value)
