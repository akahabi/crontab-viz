"""Load ScheduleFilter settings from a TOML/dict configuration block."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from crontab_viz.schedule_filter import ScheduleFilter, ScheduleFilterError


_DATETIME_FORMATS = (
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
)


def _parse_dt(value: str, field_name: str) -> datetime:
    """Parse an ISO-ish datetime string; raise ScheduleFilterError on failure."""
    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ScheduleFilterError(
        f"Cannot parse '{field_name}' value {value!r}. "
        f"Expected one of: {', '.join(_DATETIME_FORMATS)}"
    )


def filter_from_dict(config: Dict[str, Any]) -> ScheduleFilter:
    """Build a ScheduleFilter from a plain dictionary (e.g. parsed TOML).

    Recognised keys
    ---------------
    after         : str  – ISO datetime lower bound (exclusive)
    before        : str  – ISO datetime upper bound (exclusive)
    command_glob  : str  – fnmatch pattern for command
    tags          : list[str]
    limit         : int
    """
    after: Optional[datetime] = None
    before: Optional[datetime] = None

    if "after" in config:
        after = _parse_dt(str(config["after"]), "after")
    if "before" in config:
        before = _parse_dt(str(config["before"]), "before")

    tags: List[str] = [str(t) for t in config.get("tags", [])]
    command_glob: Optional[str] = config.get("command_glob") or None
    limit: int = int(config.get("limit", 0))

    return ScheduleFilter(
        after=after,
        before=before,
        command_glob=command_glob,
        tags=tags,
        limit=limit,
    )


def filter_to_dict(schedule_filter: ScheduleFilter) -> Dict[str, Any]:
    """Serialise a ScheduleFilter back to a plain dictionary."""
    d: Dict[str, Any] = {}
    if schedule_filter.after:
        d["after"] = schedule_filter.after.strftime("%Y-%m-%dT%H:%M")
    if schedule_filter.before:
        d["before"] = schedule_filter.before.strftime("%Y-%m-%dT%H:%M")
    if schedule_filter.command_glob:
        d["command_glob"] = schedule_filter.command_glob
    if schedule_filter.tags:
        d["tags"] = list(schedule_filter.tags)
    if schedule_filter.limit:
        d["limit"] = schedule_filter.limit
    return d
