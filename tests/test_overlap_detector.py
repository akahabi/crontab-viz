"""Tests for crontab_viz.overlap_detector."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from crontab_viz.overlap_detector import (
    OverlapDetectorError,
    OverlapWindow,
    find_overlaps,
    group_by_minute,
)


def _run(command: str, dt: datetime):
    """Minimal ScheduledRun-like namedtuple stand-in."""
    from types import SimpleNamespace

    entry = SimpleNamespace(command=command)
    return SimpleNamespace(entry=entry, run_time=dt)


BASE = datetime(2024, 6, 1, 9, 0, 0)


def test_find_overlaps_no_overlap():
    runs = [
        _run("job_a", BASE),
        _run("job_b", BASE + timedelta(seconds=120)),
    ]
    result = find_overlaps(runs, duration_seconds=60.0)
    assert result == []


def test_find_overlaps_exact_overlap():
    runs = [
        _run("job_a", BASE),
        _run("job_b", BASE + timedelta(seconds=30)),
    ]
    result = find_overlaps(runs, duration_seconds=60.0)
    assert len(result) == 1
    assert result[0].overlap_seconds == pytest.approx(30.0)


def test_find_overlaps_same_start_time():
    runs = [
        _run("job_a", BASE),
        _run("job_b", BASE),
    ]
    result = find_overlaps(runs, duration_seconds=60.0)
    assert len(result) == 1
    assert result[0].overlap_seconds == pytest.approx(60.0)


def test_find_overlaps_multiple_pairs():
    runs = [
        _run("job_a", BASE),
        _run("job_b", BASE + timedelta(seconds=10)),
        _run("job_c", BASE + timedelta(seconds=20)),
    ]
    result = find_overlaps(runs, duration_seconds=60.0)
    assert len(result) == 3


def test_find_overlaps_invalid_duration_raises():
    with pytest.raises(OverlapDetectorError):
        find_overlaps([], duration_seconds=0)


def test_find_overlaps_empty_runs():
    assert find_overlaps([]) == []


def test_group_by_minute_groups_correctly():
    run_a = _run("a", BASE)
    run_b = _run("b", BASE + timedelta(seconds=30))
    run_c = _run("c", BASE + timedelta(minutes=5))
    run_d = _run("d", BASE + timedelta(minutes=5, seconds=10))
    overlaps = [
        OverlapWindow(run_a, run_b, 30.0),
        OverlapWindow(run_c, run_d, 50.0),
    ]
    groups = group_by_minute(overlaps)
    assert len(groups) == 2


def test_overlap_window_str_contains_commands():
    run_a = _run("alpha", BASE)
    run_b = _run("beta", BASE + timedelta(seconds=10))
    ow = OverlapWindow(run_a, run_b, 50.0)
    text = str(ow)
    assert "alpha" in text
    assert "beta" in text
