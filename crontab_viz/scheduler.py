"""Compute next run times for cron entries using croniter."""

from datetime import datetime
from typing import Optional

try:
    from croniter import croniter
except ImportError:
    raise ImportError("croniter is required: pip install croniter")

from crontab_viz.parser import CronEntry


def next_run(entry: CronEntry, base: Optional[datetime] = None) -> datetime:
    """Return the next scheduled datetime for a CronEntry."""
    if base is None:
        base = datetime.now()
    cron = croniter(entry.schedule_expression(), base)
    return cron.get_next(datetime)


def next_n_runs(entry: CronEntry, n: int = 5, base: Optional[datetime] = None) -> list[datetime]:
    """Return the next n scheduled datetimes for a CronEntry."""
    if base is None:
        base = datetime.now()
    cron = croniter(entry.schedule_expression(), base)
    return [cron.get_next(datetime) for _ in range(n)]


def schedule_all(
    entries: list[CronEntry],
    base: Optional[datetime] = None,
) -> list[tuple[datetime, CronEntry]]:
    """Return a sorted list of (next_run_time, entry) for all entries."""
    if base is None:
        base = datetime.now()
    scheduled = []
    for entry in entries:
        try:
            run_time = next_run(entry, base=base)
            scheduled.append((run_time, entry))
        except Exception:
            pass
    scheduled.sort(key=lambda x: x[0])
    return scheduled


def detect_conflicts(
    entries: list[CronEntry],
    base: Optional[datetime] = None,
    lookahead: int = 5,
    tolerance_seconds: int = 0,
) -> list[list[tuple[datetime, CronEntry]]]:
    """Detect groups of entries that share the same scheduled run time."""
    if base is None:
        base = datetime.now()

    time_map: dict[datetime, list[CronEntry]] = {}
    for entry in entries:
        for run_time in next_n_runs(entry, n=lookahead, base=base):
            key = run_time
            if tolerance_seconds:
                from datetime import timedelta
                key = run_time.replace(second=0, microsecond=0)
            time_map.setdefault(key, []).append((run_time, entry))

    conflicts = [
        group for group in time_map.values() if len(group) > 1
    ]
    return conflicts
