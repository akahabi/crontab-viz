"""Tests for crontab_viz.formatter."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.formatter import (
    format_run,
    format_schedule_table,
    format_conflicts,
    format_summary,
)
from crontab_viz.scheduler import ScheduledRun, ConflictGroup


NOW = datetime(2024, 6, 1, 12, 0, 0)


def make_entry(command: str, expr: str = "* * * * *") -> CronEntry:
    return CronEntry(schedule_expression=expr, command=command)


def make_run(command: str, minutes_ahead: int) -> ScheduledRun:
    entry = make_entry(command)
    return ScheduledRun(entry=entry, run_at=NOW + timedelta(minutes=minutes_ahead))


def test_format_run_contains_command():
    run = make_run("backup.sh", 5)
    result = format_run(run, now=NOW)
    assert "backup.sh" in result


def test_format_run_contains_time():
    run = make_run("sync.sh", 10)
    result = format_run(run, now=NOW)
    assert "2024-06-01 12:10" in result


def test_format_run_relative_minutes():
    run = make_run("job.sh", 45)
    result = format_run(run, now=NOW)
    assert "45m" in result


def test_format_run_relative_hours():
    run = make_run("job.sh", 90)
    result = format_run(run, now=NOW)
    assert "1h" in result


def test_format_schedule_table_empty():
    result = format_schedule_table([], now=NOW)
    assert "No upcoming runs" in result


def test_format_schedule_table_sorted():
    runs = [make_run("second.sh", 20), make_run("first.sh", 5)]
    result = format_schedule_table(runs, now=NOW)
    idx_first = result.index("first.sh")
    idx_second = result.index("second.sh")
    assert idx_first < idx_second


def test_format_schedule_table_contains_header():
    runs = [make_run("job.sh", 1)]
    result = format_schedule_table(runs, now=NOW)
    assert "SCHEDULED AT" in result
    assert "COMMAND" in result


def test_format_conflicts_no_conflicts():
    result = format_conflicts([])
    assert "No conflicts" in result


def test_format_conflicts_shows_commands():
    entries = [make_entry("alpha.sh"), make_entry("beta.sh")]
    group = ConflictGroup(run_at=NOW, entries=entries)
    result = format_conflicts([group])
    assert "alpha.sh" in result
    assert "beta.sh" in result
    assert "2024-06-01 12:00" in result


def test_format_summary_no_conflicts():
    result = format_summary(5, 20, 0)
    assert "0 conflicts" in result
    assert "5" in result
    assert "20" in result


def test_format_summary_with_conflicts():
    result = format_summary(3, 10, 2)
    assert "2 conflict" in result
