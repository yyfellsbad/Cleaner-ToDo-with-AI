from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


def _parse_datetime(s: str) -> datetime:
    """兼容 '2026-05-27' 和 '2026-05-27T14:30:00' 两种格式。"""
    if "T" in s or len(s) > 10:
        return datetime.fromisoformat(s)
    return datetime.strptime(s, "%Y-%m-%d")


def _fmt_db(dt: datetime) -> str:
    """有时间时输出 '2026-05-27T14:30:00'，无时间只输出 '2026-05-27'。"""
    if dt.hour == 0 and dt.minute == 0:
        return dt.strftime("%Y-%m-%d")
    return dt.isoformat()


@dataclass(slots=True)
class TaskRecord:
    id: int | None = None
    name: str = ""
    date: datetime = field(default_factory=lambda: datetime.now().replace(second=0, microsecond=0))
    end_date: datetime | None = None
    description: str = ""
    completed: bool = False
    repeat_days: int = 0
    repeat_mode: str = "once"  # "once" | "each"
    completed_dates: list[str] = field(default_factory=list)  # ["2026-06-01", ...]

    @classmethod
    def from_row(cls, row: Any) -> "TaskRecord":
        def _get(key_or_idx, default=None):
            try:
                return row[key_or_idx]
            except (KeyError, IndexError):
                return default

        id_val = _get("id", _get(0))
        name_val = _get("name", _get(1, ""))
        date_val = _get("date", _get(2, ""))
        end_date_val = _get("end_date", _get(3))
        desc_val = _get("description", _get(4, ""))
        completed_val = _get("completed", _get(5, 0))
        repeat_days_val = _get("repeat_days", _get(6, 0)) or 0
        repeat_mode_val = _get("repeat_mode", _get(7, "once")) or "once"
        completed_dates_raw = _get("completed_dates", _get(8, "[]")) or "[]"

        # completed_dates 解析
        if isinstance(completed_dates_raw, str):
            try:
                cd_list = json.loads(completed_dates_raw)
            except (json.JSONDecodeError, TypeError):
                cd_list = []
        elif isinstance(completed_dates_raw, list):
            cd_list = completed_dates_raw
        else:
            cd_list = []

        return cls(
            id=int(id_val) if id_val is not None else None,
            name=str(name_val),
            date=_parse_datetime(str(date_val)),
            end_date=_parse_datetime(str(end_date_val)) if end_date_val else None,
            description=str(desc_val or ""),
            completed=bool(completed_val),
            repeat_days=int(repeat_days_val),
            repeat_mode=str(repeat_mode_val),
            completed_dates=[str(d) for d in cd_list],
        )

    def to_db_values(self) -> tuple[str, str, str | None, str, int, int, str, str]:
        return (
            self.name,
            _fmt_db(self.date),
            _fmt_db(self.end_date) if self.end_date else None,
            self.description,
            int(self.completed),
            self.repeat_days,
            self.repeat_mode,
            json.dumps(self.completed_dates, ensure_ascii=False),
        )

    # ── repeat helpers ─────────────────────────────────────

    @property
    def is_recurring(self) -> bool:
        return self.repeat_days > 0 and self.end_date is not None

    @property
    def repeat_occurrences(self) -> list[date]:
        """返回所有应完成的日期列表（each 模式）。"""
        if not self.is_recurring:
            return []
        start = self.date.date()
        end = self.end_date.date()
        days = []
        d = start
        while d <= end:
            days.append(d)
            d = date.fromordinal(d.toordinal() + self.repeat_days)
        return days

    @property
    def all_occurrences_done(self) -> bool:
        """each 模式下所有日期是否都已完成。"""
        if not self.is_recurring or self.repeat_mode != "each":
            return self.completed
        occurrences = self.repeat_occurrences
        if not occurrences:
            return self.completed
        return all(d.isoformat() in self.completed_dates for d in occurrences)

    def occurrence_done(self, d: date) -> bool:
        """检查某一天是否已完成。"""
        return d.isoformat() in self.completed_dates

    def mark_occurrence(self, d: date) -> bool:
        """标记某一天为已完成。返回 True 如果是新标记。"""
        key = d.isoformat()
        if key in self.completed_dates:
            return False
        self.completed_dates.append(key)
        if self.repeat_mode == "each" and self.all_occurrences_done:
            self.completed = True
        return True
