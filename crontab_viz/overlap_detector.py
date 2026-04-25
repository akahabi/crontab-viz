"""Detect temporal overlaps between scheduled cron runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Tuple

from crontab_viz.scheduler import ScheduledRun


@dataclass
class OverlapWindow:
    """Two runs whose execution windows overlap."""

    run_a: ScheduledRun
    run_b: ScheduledRun
    overlap_seconds: float

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"OVERLAP: '{self.run_a.entry.command}' and "
            f"'{self.run_b.entry.command}' overlap by "
            f"{self.overlap_seconds:.0f}s at {self.run_a.run_time:%H:%M}"
        )


class OverlapDetectorError(Exception):
    """Raised when overlap detection is mis-configured."""


def _window_end(run: ScheduledRun, duration_seconds: float) -> datetime:
    return run.run_time + timedelta(seconds=duration_seconds)


def find_overlaps(
    runs: List[ScheduledRun],
    duration_seconds: float = 60.0,
) -> List[OverlapWindow]:
    """Return all pairs of runs whose assumed execution windows overlap.

    Args:
        runs: Flat list of scheduled runs (any order).
        duration_seconds: Assumed execution duration for every job.

    Returns:
        List of :class:`OverlapWindow` instances, sorted by overlap start.
    """
    if duration_seconds <= 0:
        raise OverlapDetectorError("duration_seconds must be positive")

    sorted_runs = sorted(runs, key=lambda r: r.run_time)
    overlaps: List[OverlapWindow] = []

    for i, a in enumerate(sorted_runs):
        end_a = _window_end(a, duration_seconds)
        for b in sorted_runs[i + 1 :]:
            if b.run_time >= end_a:
                break  # no further run can overlap with a
            end_b = _window_end(b, duration_seconds)
            overlap_end = min(end_a, end_b)
            overlap_start = max(a.run_time, b.run_time)
            overlap_secs = (overlap_end - overlap_start).total_seconds()
            if overlap_secs > 0:
                overlaps.append(OverlapWindow(a, b, overlap_secs))

    return overlaps


def group_by_minute(
    overlaps: List[OverlapWindow],
) -> dict[str, List[OverlapWindow]]:
    """Group overlap windows by the minute they start (HH:MM key)."""
    groups: dict[str, List[OverlapWindow]] = {}
    for ow in overlaps:
        key = ow.run_a.run_time.strftime("%Y-%m-%d %H:%M")
        groups.setdefault(key, []).append(ow)
    return groups
