"""Tests for crontab_viz.history."""

import json
from pathlib import Path

import pytest

from crontab_viz.history import (
    HistoryError,
    RunRecord,
    append_record,
    load_history,
    prune_history,
)


def _record(cmd: str = "echo hi", scheduled: str = "2024-01-01T00:00:00") -> RunRecord:
    return RunRecord(command=cmd, scheduled_at=scheduled)


def test_load_history_missing_file_returns_empty(tmp_path):
    result = load_history(tmp_path / "nonexistent.json")
    assert result == []


def test_load_history_reads_records(tmp_path):
    p = tmp_path / "hist.json"
    records = [_record("job1"), _record("job2")]
    p.write_text(json.dumps([r.as_dict() for r in records]), encoding="utf-8")
    loaded = load_history(p)
    assert len(loaded) == 2
    assert loaded[0].command == "job1"


def test_load_history_malformed_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("NOT JSON", encoding="utf-8")
    with pytest.raises(HistoryError):
        load_history(p)


def test_append_record_creates_file(tmp_path):
    p = tmp_path / "sub" / "hist.json"
    append_record(p, _record())
    assert p.exists()
    data = json.loads(p.read_text())
    assert len(data) == 1


def test_append_record_accumulates(tmp_path):
    p = tmp_path / "hist.json"
    append_record(p, _record("a"))
    append_record(p, _record("b"))
    records = load_history(p)
    assert [r.command for r in records] == ["a", "b"]


def test_prune_history_removes_oldest(tmp_path):
    p = tmp_path / "hist.json"
    for i in range(10):
        append_record(p, _record(f"job{i}"))
    removed = prune_history(p, keep=6)
    assert removed == 4
    remaining = load_history(p)
    assert len(remaining) == 6
    assert remaining[0].command == "job4"


def test_prune_history_no_op_when_under_limit(tmp_path):
    p = tmp_path / "hist.json"
    append_record(p, _record())
    removed = prune_history(p, keep=100)
    assert removed == 0


def test_run_record_from_dict_roundtrip():
    rec = _record("ping", "2024-06-15T12:00:00")
    rec2 = RunRecord.from_dict(rec.as_dict())
    assert rec2.command == rec.command
    assert rec2.scheduled_at == rec.scheduled_at
