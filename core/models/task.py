from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(slots=True)
class TaskRecord:
    id: int | None = None
    name: str = ""
    date: date = field(default_factory=date.today)
    completed: bool = False

    @classmethod
    def from_row(cls, row: Any) -> "TaskRecord":
        if hasattr(row, "keys"):
            return cls(
                id=int(row["id"]) if row["id"] is not None else None,
                name=str(row["name"]),
                date=date.fromisoformat(str(row["date"])),
                completed=bool(row["completed"]),
            )

        return cls(
            id=int(row[0]) if row[0] is not None else None,
            name=str(row[1]),
            date=date.fromisoformat(str(row[2])),
            completed=bool(row[3]),
        )

    def to_db_values(self) -> tuple[str, str, int]:
        return self.name, self.date.isoformat(), int(self.completed)
