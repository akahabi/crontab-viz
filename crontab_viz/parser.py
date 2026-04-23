"""Crontab entry parser module."""

from dataclasses import dataclass, field
from typing import Optional
import re

CRON_FIELD_NAMES = ["minute", "hour", "day", "month", "weekday"]

SPECIAL_ALIASES = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


@dataclass
class CronEntry:
    raw: str
    minute: str
    hour: str
    day: str
    month: str
    weekday: str
    command: str
    comment: Optional[str] = None
    line_number: Optional[int] = None
    tags: list = field(default_factory=list)

    def schedule_expression(self) -> str:
        return f"{self.minute} {self.hour} {self.day} {self.month} {self.weekday}"

    def __str__(self) -> str:
        return f"[line {self.line_number}] {self.schedule_expression()} {self.command}"


class CronParseError(Exception):
    pass


def parse_line(line: str, line_number: int = None) -> Optional[CronEntry]:
    """Parse a single crontab line into a CronEntry."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    comment = None
    if " #" in line:
        line, comment = line.split(" #", 1)
        comment = comment.strip()
        line = line.strip()

    for alias, expansion in SPECIAL_ALIASES.items():
        if line.startswith(alias):
            command = line[len(alias):].strip()
            line = f"{expansion} {command}"
            break

    parts = line.split(None, 5)
    if len(parts) < 6:
        raise CronParseError(
            f"Invalid crontab entry at line {line_number}: '{line}'"
        )

    minute, hour, day, month, weekday, command = parts
    return CronEntry(
        raw=line,
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        weekday=weekday,
        command=command,
        comment=comment,
        line_number=line_number,
    )


def parse_crontab(text: str) -> list[CronEntry]:
    """Parse a full crontab file text and return valid entries."""
    entries = []
    errors = []
    for i, line in enumerate(text.splitlines(), start=1):
        try:
            entry = parse_line(line, line_number=i)
            if entry:
                entries.append(entry)
        except CronParseError as e:
            errors.append(str(e))
    if errors:
        import warnings
        for err in errors:
            warnings.warn(err)
    return entries
