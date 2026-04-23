"""Tests for the scheduler module."""

from datetime import datetime
import pytest
from crontab_viz.parser import parse_line
from crontab_viz.scheduler import next_run, next_n_runs, schedule_all, detect_conflicts


BASE_TIME = datetime(2024, 1, 15, 12, 0, 0)  # Monday noon


def make_entry(cron_str: str):
    return parse_line(cron_str, line_number=1)


def test_next_run_returns_future_datetime():
    entry = make_entry("*/5 * * * * /bin/task.sh")
    result = next_run(entry, base=BASE_TIME)
    assert isinstance(result, datetime)
    assert result > BASE_TIME


def test_next_run_every_5_minutes():
    entry = make_entry("*/5 * * * * /bin/task.sh")
    result = next_run(entry, base=BASE_TIME)
    assert result.minute % 5 == 0


def test_next_n_runs_count():
    entry = make_entry("0 * * * * /bin/hourly.sh")
    results = next_n_runs(entry, n=5, base=BASE_TIME)
    assert len(results) == 5
    assert all(isinstance(r, datetime) for r in results)


def test_next_n_runs_are_ascending():
    entry = make_entry("0 * * * * /bin/hourly.sh")
    results = next_n_runs(entry, n=5, base=BASE_TIME)
    for i in range(1, len(results)):
        assert results[i] > results[i - 1]


def test_schedule_all_returns_sorted():
    entries = [
        make_entry("0 2 * * * /bin/a.sh"),
        make_entry("0 1 * * * /bin/b.sh"),
        make_entry("0 3 * * * /bin/c.sh"),
    ]
    scheduled = schedule_all(entries, base=BASE_TIME)
    times = [t for t, _ in scheduled]
    assert times == sorted(times)


def test_schedule_all_includes_all_entries():
    entries = [
        make_entry("*/10 * * * * /bin/x.sh"),
        make_entry("*/15 * * * * /bin/y.sh"),
    ]
    scheduled = schedule_all(entries, base=BASE_TIME)
    assert len(scheduled) == 2


def test_detect_conflicts_finds_overlap():
    # Both run at minute 0 of every hour
    entries = [
        make_entry("0 * * * * /bin/job1.sh"),
        make_entry("0 * * * * /bin/job2.sh"),
    ]
    conflicts = detect_conflicts(entries, base=BASE_TIME, lookahead=3)
    assert len(conflicts) > 0
    for group in conflicts:
        assert len(group) >= 2


def test_detect_conflicts_no_overlap():
    entries = [
        make_entry("0 1 * * * /bin/job1.sh"),
        make_entry("0 2 * * * /bin/job2.sh"),
    ]
    conflicts = detect_conflicts(entries, base=BASE_TIME, lookahead=3)
    assert len(conflicts) == 0
