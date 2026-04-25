"""Tests for crontab_viz.schedule_filter_config."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from crontab_viz.schedule_filter import ScheduleFilter, ScheduleFilterError
from crontab_viz.schedule_filter_config import filter_from_dict, filter_to_dict


# --- filter_from_dict ---

def test_empty_dict_gives_default_filter() -> None:
    f = filter_from_dict({})
    assert f.after is None
    assert f.before is None
    assert f.command_glob is None
    assert f.tags == []
    assert f.limit == 0


def test_parses_after_datetime() -> None:
    f = filter_from_dict({"after": "2024-06-01T09:00"})
    assert f.after == datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc)


def test_parses_before_date_only() -> None:
    f = filter_from_dict({"before": "2024-07-01"})
    assert f.before == datetime(2024, 7, 1, 0, 0, tzinfo=timezone.utc)


def test_parses_space_separated_datetime() -> None:
    f = filter_from_dict({"after": "2024-06-01 08:30"})
    assert f.after is not None
    assert f.after.hour == 8
    assert f.after.minute == 30


def test_invalid_datetime_string_raises() -> None:
    with pytest.raises(ScheduleFilterError, match="after"):
        filter_from_dict({"after": "not-a-date"})


def test_parses_tags_list() -> None:
    f = filter_from_dict({"tags": ["nightly", "db"]})
    assert f.tags == ["nightly", "db"]


def test_parses_command_glob() -> None:
    f = filter_from_dict({"command_glob": "*/backup*"})
    assert f.command_glob == "*/backup*"


def test_parses_limit() -> None:
    f = filter_from_dict({"limit": 10})
    assert f.limit == 10


def test_invalid_window_propagates() -> None:
    """filter_from_dict should surface ScheduleFilterError from ScheduleFilter."""
    with pytest.raises(ScheduleFilterError):
        filter_from_dict({"after": "2024-06-02T00:00", "before": "2024-06-01T00:00"})


# --- filter_to_dict ---

def test_round_trip_preserves_values() -> None:
    original = ScheduleFilter(
        after=datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc),
        before=datetime(2024, 6, 1, 18, 0, tzinfo=timezone.utc),
        command_glob="*/job*",
        tags=["nightly"],
        limit=5,
    )
    d = filter_to_dict(original)
    restored = filter_from_dict(d)
    assert restored.after == original.after
    assert restored.before == original.before
    assert restored.command_glob == original.command_glob
    assert restored.tags == original.tags
    assert restored.limit == original.limit


def test_empty_filter_to_dict_is_empty() -> None:
    assert filter_to_dict(ScheduleFilter()) == {}


def test_to_dict_omits_none_fields() -> None:
    f = ScheduleFilter(limit=3)
    d = filter_to_dict(f)
    assert "after" not in d
    assert "before" not in d
    assert "command_glob" not in d
    assert d["limit"] == 3
