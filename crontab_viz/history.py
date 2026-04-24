"""Track and persist a history of cron job run events."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class HistoryError(Exception):
    """Raised when the history store cannot be read or written."""


@dataclass
class RunRecord:
    command: str
    scheduled_at: str  # ISO-8601
    recorded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    note: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RunRecord":
        return cls(
            command=data["command"],
            scheduled_at=data["scheduled_at"],
            recorded_at=data.get("recorded_at", ""),
            note=data.get("note"),
        )


def load_history(path: Path) -> List[RunRecord]:
    """Load persisted run records from *path*.

    Returns an empty list when the file does not yet exist.
    Raises :class:`HistoryError` on malformed JSON.
    """
    if not path.exists():
        return []
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return [RunRecord.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise HistoryError(f"Cannot parse history file {path}: {exc}") from exc


def append_record(path: Path, record: RunRecord) -> None:
    """Append *record* to the JSON history file at *path*.

    Creates the file (and parent directories) if necessary.
    Raises :class:`HistoryError` on I/O failure.
    """
    try:
        records = load_history(path)
        records.append(record)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps([r.as_dict() for r in records], indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise HistoryError(f"Cannot write history file {path}: {exc}") from exc


def prune_history(path: Path, keep: int = 500) -> int:
    """Remove oldest records so at most *keep* entries remain.

    Returns the number of records removed.
    """
    records = load_history(path)
    if len(records) <= keep:
        return 0
    removed = len(records) - keep
    trimmed = records[-keep:]
    path.write_text(
        json.dumps([r.as_dict() for r in trimmed], indent=2),
        encoding="utf-8",
    )
    return removed
