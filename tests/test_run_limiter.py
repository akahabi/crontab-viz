"""Tests for crontab_viz.run_limiter."""
from __future__ import annotations

import pytest

from crontab_viz.run_limiter import RunLimiter, RunLimiterError

CMD = "backup.sh"
NOW = 1_000_000.0  # fixed epoch second for determinism


# ---------------------------------------------------------------------------
# Construction / validation
# ---------------------------------------------------------------------------


def test_defaults_are_valid():
    limiter = RunLimiter()
    assert limiter.window_seconds == 3600.0
    assert limiter.max_per_window == 10


def test_invalid_window_raises():
    with pytest.raises(RunLimiterError, match="window_seconds"):
        RunLimiter(window_seconds=0)


def test_invalid_max_raises():
    with pytest.raises(RunLimiterError, match="max_per_window"):
        RunLimiter(max_per_window=0)


# ---------------------------------------------------------------------------
# is_allowed + record
# ---------------------------------------------------------------------------


def test_allowed_before_any_record():
    limiter = RunLimiter(max_per_window=3, window_seconds=60)
    assert limiter.is_allowed(CMD, now=NOW) is True


def test_not_allowed_after_max_records():
    limiter = RunLimiter(max_per_window=2, window_seconds=60)
    limiter.record(CMD, now=NOW)
    limiter.record(CMD, now=NOW + 1)
    assert limiter.is_allowed(CMD, now=NOW + 2) is False


def test_allowed_again_after_window_expires():
    limiter = RunLimiter(max_per_window=1, window_seconds=60)
    limiter.record(CMD, now=NOW)
    # still blocked inside window
    assert limiter.is_allowed(CMD, now=NOW + 59) is False
    # allowed after window passes (strictly > window_seconds)
    assert limiter.is_allowed(CMD, now=NOW + 61) is True


# ---------------------------------------------------------------------------
# count
# ---------------------------------------------------------------------------


def test_count_zero_initially():
    limiter = RunLimiter()
    assert limiter.count(CMD, now=NOW) == 0


def test_count_increases_with_records():
    limiter = RunLimiter(window_seconds=120)
    limiter.record(CMD, now=NOW)
    limiter.record(CMD, now=NOW + 10)
    assert limiter.count(CMD, now=NOW + 10) == 2


def test_count_drops_after_eviction():
    limiter = RunLimiter(window_seconds=30)
    limiter.record(CMD, now=NOW)
    limiter.record(CMD, now=NOW + 20)
    # first record falls outside window
    assert limiter.count(CMD, now=NOW + 31) == 1


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


def test_reset_single_command():
    limiter = RunLimiter(max_per_window=1, window_seconds=60)
    limiter.record(CMD, now=NOW)
    limiter.reset(CMD)
    assert limiter.is_allowed(CMD, now=NOW) is True


def test_reset_all_commands():
    limiter = RunLimiter(max_per_window=1, window_seconds=60)
    limiter.record(CMD, now=NOW)
    limiter.record("other.sh", now=NOW)
    limiter.reset()
    assert limiter.count(CMD, now=NOW) == 0
    assert limiter.count("other.sh", now=NOW) == 0


def test_reset_unknown_command_is_noop():
    limiter = RunLimiter()
    limiter.reset("nonexistent.sh")  # should not raise
