"""Tests for crontab_viz.tag_filter."""

from __future__ import annotations

import pytest

from crontab_viz.parser import CronEntry
from crontab_viz.tag_filter import (
    TagFilterError,
    extract_tags,
    filter_by_tags,
    summarise_tags,
)


def _entry(command: str) -> CronEntry:
    return CronEntry(
        schedule="* * * * *",
        command=command,
        raw=f"* * * * * {command}",
    )


# --- extract_tags ---

def test_extract_tags_single():
    entry = _entry("/usr/bin/backup.sh #tag:backup")
    assert extract_tags(entry) == ["backup"]


def test_extract_tags_multiple():
    entry = _entry("/usr/bin/sync.sh #tag:sync #tag:nightly")
    assert extract_tags(entry) == ["sync", "nightly"]


def test_extract_tags_none():
    entry = _entry("/usr/bin/plain.sh")
    assert extract_tags(entry) == []


def test_extract_tags_ignores_plain_comments():
    entry = _entry("/usr/bin/x.sh # just a comment")
    assert extract_tags(entry) == []


# --- filter_by_tags ---

def test_filter_by_tags_include_keeps_matching():
    entries = [
        _entry("/bin/a #tag:backup"),
        _entry("/bin/b #tag:report"),
        _entry("/bin/c"),
    ]
    result = filter_by_tags(entries, include=["backup"])
    assert len(result) == 1
    assert "backup" in result[0].command


def test_filter_by_tags_include_multiple_tags():
    entries = [
        _entry("/bin/a #tag:backup"),
        _entry("/bin/b #tag:report"),
        _entry("/bin/c #tag:nightly"),
    ]
    result = filter_by_tags(entries, include=["backup", "nightly"])
    assert len(result) == 2


def test_filter_by_tags_exclude_removes_matching():
    entries = [
        _entry("/bin/a #tag:backup"),
        _entry("/bin/b #tag:report"),
    ]
    result = filter_by_tags(entries, exclude=["backup"])
    assert len(result) == 1
    assert "report" in result[0].command


def test_filter_by_tags_include_then_exclude():
    entries = [
        _entry("/bin/a #tag:backup #tag:slow"),
        _entry("/bin/b #tag:backup"),
    ]
    result = filter_by_tags(entries, include=["backup"], exclude=["slow"])
    assert len(result) == 1
    assert "/bin/b" in result[0].command


def test_filter_by_tags_empty_include_raises():
    with pytest.raises(TagFilterError):
        filter_by_tags([_entry("/bin/x")], include=[])


def test_filter_by_tags_no_filters_returns_all():
    entries = [_entry("/bin/a"), _entry("/bin/b")]
    assert filter_by_tags(entries) == entries


# --- summarise_tags ---

def test_summarise_tags_counts():
    entries = [
        _entry("/bin/a #tag:backup"),
        _entry("/bin/b #tag:backup #tag:nightly"),
        _entry("/bin/c #tag:nightly"),
    ]
    summary = summarise_tags(entries)
    assert summary["backup"] == 2
    assert summary["nightly"] == 2


def test_summarise_tags_empty():
    assert summarise_tags([]) == {}


def test_summarise_tags_no_tags():
    entries = [_entry("/bin/plain.sh")]
    assert summarise_tags(entries) == {}
