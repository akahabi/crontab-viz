"""Tests for crontab_viz.schedule_filter."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import ScheduledRun
from crontab_viz.schedule_filter import (
    ScheduleFilter,
    ScheduleFilterError,
    apply_filter,
    summarise_filter,
)


DT = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)


def _entry(command: str = "/usr/bin/job") -> CronEntry:
    return CronEntry(schedule="* * * * *", command=command, raw=f"* * * * * {command}")


def _run(offset_minutes: int = 0, command: str = "/usr/bin/job") -> ScheduledRun:
    t = datetime(2024, 6, 1, 12, offset_minutes, tzinfo=timezone.utc)
    return ScheduledRun(entry=_entry(command), run_time=t)


# --- ScheduleFilter validation ---

def test_invalid_window_raises() -> None:
    after = datetime(2024, 6, 1, 13, 0, tzinfo=timezone.utc)
    before = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ScheduleFilterError):
        ScheduleFilter(after=after, before=before)


def test_equal_window_raises() -> None:
    t = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ScheduleFilterError):
        ScheduleFilter(after=t, before=t)


def test_negative_limit_raises() -> None:
    with pytest.raises(ScheduleFilterError):
        ScheduleFilter(limit=-1)


# --- apply_filter ---

def test_apply_filter_no_criteria_returns_all() -> None:
    runs = [_run(0), _run(5), _run(10)]
    assert apply_filter(runs, ScheduleFilter()) == runs


def test_apply_filter_after_excludes_early() -> None:
    after = datetime(2024, 6, 1, 12, 3, tzinfo=timezone.utc)
    runs = [_run(0), _run(5), _run(10)]
    result = apply_filter(runs, ScheduleFilter(after=after))
    assert all(r.run_time > after for r in result)
    assert len(result) == 2


def test_apply_filter_before_excludes_late() -> None:
    before = datetime(2024, 6, 1, 12, 8, tzinfo=timezone.utc)
    runs = [_run(0), _run(5), _run(10)]
    result = apply_filter(runs, ScheduleFilter(before=before))
    assert len(result) == 2


def test_apply_filter_command_glob_matches() -> None:
    runs = [_run(command="/usr/bin/backup"), _run(command="/usr/bin/cleanup")]
    result = apply_filter(runs, ScheduleFilter(command_glob="*/backup"))
    assert len(result) == 1
    assert result[0].entry.command == "/usr/bin/backup"


def test_apply_filter_command_glob_no_match() -> None:
    runs = [_run(command="/usr/bin/other")]
    result = apply_filter(runs, ScheduleFilter(command_glob="*/backup"))
    assert result == []


def test_apply_filter_tags_match() -> None:
    runs = [
        _run(command="/bin/job #nightly #db"),
        _run(command="/bin/job #nightly"),
    ]
    result = apply_filter(runs, ScheduleFilter(tags=["nightly", "db"]))
    assert len(result) == 1


def test_apply_filter_limit_truncates() -> None:
    runs = [_run(i) for i in range(10)]
    result = apply_filter(runs, ScheduleFilter(limit=3))
    assert len(result) == 3


def test_apply_filter_limit_zero_means_all() -> None:
    runs = [_run(i) for i in range(5)]
    result = apply_filter(runs, ScheduleFilter(limit=0))
    assert len(result) == 5


# --- summarise_filter ---

def test_summarise_no_filters() -> None:
    assert summarise_filter(ScheduleFilter()) == "no filters"


def test_summarise_includes_limit() -> None:
    assert "limit=5" in summarise_filter(ScheduleFilter(limit=5))


def test_summarise_includes_tags() -> None:
    summary = summarise_filter(ScheduleFilter(tags=["nightly"]))
    assert "nightly" in summary
