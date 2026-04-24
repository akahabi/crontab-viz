"""Tests for crontab_viz.history_reporter."""

from crontab_viz.history import RunRecord
from crontab_viz.history_reporter import (
    format_history_table,
    most_frequent_commands,
    records_for_command,
    summarise_history,
)


def _rec(cmd: str, scheduled: str = "2024-01-01T00:00:00") -> RunRecord:
    return RunRecord(command=cmd, scheduled_at=scheduled)


def test_most_frequent_commands_order():
    records = [_rec("a"), _rec("b"), _rec("a"), _rec("a"), _rec("b")]
    result = most_frequent_commands(records, top_n=2)
    assert result[0] == ("a", 3)
    assert result[1] == ("b", 2)


def test_most_frequent_commands_empty():
    assert most_frequent_commands([]) == []


def test_records_for_command_filters():
    records = [_rec("foo"), _rec("bar"), _rec("foo")]
    result = records_for_command(records, "foo")
    assert len(result) == 2
    assert all(r.command == "foo" for r in result)


def test_records_for_command_no_match():
    records = [_rec("foo")]
    assert records_for_command(records, "baz") == []


def test_format_history_table_empty():
    out = format_history_table([])
    assert "No history" in out


def test_format_history_table_contains_command():
    records = [_rec("my-cron-job")]
    out = format_history_table(records)
    assert "my-cron-job" in out


def test_format_history_table_respects_limit():
    records = [_rec(f"job{i}") for i in range(30)]
    out = format_history_table(records, limit=5)
    # Only 5 data rows + header + separator = 7 lines
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) == 7


def test_summarise_history_empty():
    assert "empty" in summarise_history([])


def test_summarise_history_counts():
    records = [_rec("a", "2024-01-01T00:00:00"), _rec("b", "2024-06-01T00:00:00")]
    summary = summarise_history(records)
    assert "2" in summary
    assert "2024-01-01" in summary
    assert "2024-06-01" in summary
