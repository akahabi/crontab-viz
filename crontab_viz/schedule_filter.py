"""Filter scheduled runs by time window, command pattern, or tag."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Sequence

from crontab_viz.scheduler import ScheduledRun


class ScheduleFilterError(ValueError):
    """Raised when filter configuration is invalid."""


@dataclass
class ScheduleFilter:
    """Criteria used to narrow a list of ScheduledRuns."""

    after: Optional[datetime] = None
    before: Optional[datetime] = None
    command_glob: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    limit: int = 0  # 0 means no limit

    def __post_init__(self) -> None:
        if self.after and self.before and self.after >= self.before:
            raise ScheduleFilterError(
                "'after' must be strictly earlier than 'before'"
            )
        if self.limit < 0:
            raise ScheduleFilterError("'limit' must be >= 0")


def _run_tags(run: ScheduledRun) -> List[str]:
    """Extract #tag tokens from a run's command string."""
    return re.findall(r"#([\w-]+)", run.entry.command)


def apply_filter(
    runs: Sequence[ScheduledRun],
    schedule_filter: ScheduleFilter,
) -> List[ScheduledRun]:
    """Return runs that satisfy every criterion in *schedule_filter*."""
    result: List[ScheduledRun] = []

    for run in runs:
        if schedule_filter.after and run.run_time <= schedule_filter.after:
            continue
        if schedule_filter.before and run.run_time >= schedule_filter.before:
            continue
        if schedule_filter.command_glob and not fnmatch.fnmatch(
            run.entry.command, schedule_filter.command_glob
        ):
            continue
        if schedule_filter.tags:
            run_tag_set = set(_run_tags(run))
            if not all(t in run_tag_set for t in schedule_filter.tags):
                continue
        result.append(run)

    if schedule_filter.limit:
        result = result[: schedule_filter.limit]

    return result


def summarise_filter(schedule_filter: ScheduleFilter) -> str:
    """Return a human-readable description of the active filter criteria."""
    parts: List[str] = []
    if schedule_filter.after:
        parts.append(f"after {schedule_filter.after.isoformat(timespec='minutes')}")
    if schedule_filter.before:
        parts.append(f"before {schedule_filter.before.isoformat(timespec='minutes')}")
    if schedule_filter.command_glob:
        parts.append(f"command~={schedule_filter.command_glob!r}")
    if schedule_filter.tags:
        parts.append("tags=[" + ", ".join(schedule_filter.tags) + "]")
    if schedule_filter.limit:
        parts.append(f"limit={schedule_filter.limit}")
    return ", ".join(parts) if parts else "no filters"
