from __future__ import annotations

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

    @classmethod
    def from_row(cls, row: Any) -> "TaskRecord":
        if hasattr(row, "keys"):
            return cls(
                id=int(row["id"]) if row["id"] is not None else None,
                name=str(row["name"]),
                date=_parse_datetime(str(row["date"])),
                end_date=(
                    _parse_datetime(str(row["end_date"]))
                    if row["end_date"]
                    else None
                ),
                description=str(row["description"] or ""),
                completed=bool(row["completed"]),
            )

        return cls(
            id=int(row[0]) if row[0] is not None else None,
            name=str(row[1]),
            date=_parse_datetime(str(row[2])),
            end_date=_parse_datetime(str(row[3])) if row[3] else None,
            description=str(row[4] or ""),
            completed=bool(row[5]),
        )

    def to_db_values(self) -> tuple[str, str, str | None, str, int]:
        return (
            self.name,
            _fmt_db(self.date),
            _fmt_db(self.end_date) if self.end_date else None,
            self.description,
            int(self.completed),
        )
