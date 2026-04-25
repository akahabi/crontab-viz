"""Tests for crontab_viz.overlap_config."""
from __future__ import annotations

import pytest

from crontab_viz.overlap_config import OverlapConfig, OverlapConfigError


def test_defaults_are_valid():
    cfg = OverlapConfig()
    assert cfg.duration_seconds == 60.0
    assert cfg.ignored_commands == []
    assert cfg.min_overlap_seconds == 0.0


def test_invalid_duration_raises():
    with pytest.raises(OverlapConfigError):
        OverlapConfig(duration_seconds=0)


def test_negative_duration_raises():
    with pytest.raises(OverlapConfigError):
        OverlapConfig(duration_seconds=-5.0)


def test_negative_min_overlap_raises():
    with pytest.raises(OverlapConfigError):
        OverlapConfig(min_overlap_seconds=-1.0)


def test_is_ignored_returns_true_for_listed_command():
    cfg = OverlapConfig(ignored_commands=["/usr/bin/backup"])
    assert cfg.is_ignored("/usr/bin/backup") is True


def test_is_ignored_returns_false_for_unlisted_command():
    cfg = OverlapConfig(ignored_commands=["/usr/bin/backup"])
    assert cfg.is_ignored("/usr/bin/cleanup") is False


def test_passes_threshold_above_minimum():
    cfg = OverlapConfig(min_overlap_seconds=10.0)
    assert cfg.passes_threshold(15.0) is True


def test_passes_threshold_below_minimum():
    cfg = OverlapConfig(min_overlap_seconds=10.0)
    assert cfg.passes_threshold(5.0) is False


def test_passes_threshold_exactly_minimum():
    cfg = OverlapConfig(min_overlap_seconds=10.0)
    assert cfg.passes_threshold(10.0) is True
