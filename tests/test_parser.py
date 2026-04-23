"""Tests for the crontab parser module."""

import pytest
from crontab_viz.parser import parse_line, parse_crontab, CronParseError, CronEntry


def test_parse_simple_entry():
    entry = parse_line("*/5 * * * * /usr/bin/backup.sh", line_number=1)
    assert isinstance(entry, CronEntry)
    assert entry.minute == "*/5"
    assert entry.hour == "*"
    assert entry.command == "/usr/bin/backup.sh"
    assert entry.line_number == 1


def test_parse_comment_line_returns_none():
    assert parse_line("# this is a comment") is None


def test_parse_empty_line_returns_none():
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_parse_inline_comment():
    entry = parse_line("0 2 * * * /bin/cleanup.sh #nightly cleanup", line_number=3)
    assert entry.comment == "nightly cleanup"
    assert entry.command == "/bin/cleanup.sh"


def test_parse_special_alias_daily():
    entry = parse_line("@daily /bin/daily_task.sh", line_number=5)
    assert entry.minute == "0"
    assert entry.hour == "0"
    assert entry.command == "/bin/daily_task.sh"


def test_parse_special_alias_hourly():
    entry = parse_line("@hourly /bin/hourly_task.sh")
    assert entry.minute == "0"
    assert entry.hour == "*"


def test_parse_invalid_entry_raises():
    with pytest.raises(CronParseError):
        parse_line("* * * /incomplete", line_number=10)


def test_parse_crontab_full_text():
    text = """
# My crontab
*/10 * * * * /usr/bin/monitor.sh
0 0 * * * /usr/bin/nightly.sh
@weekly /usr/bin/weekly_report.sh
"""
    entries = parse_crontab(text)
    assert len(entries) == 3
    assert entries[0].minute == "*/10"
    assert entries[1].hour == "0"
    assert entries[2].weekday == "0"


def test_schedule_expression():
    entry = parse_line("30 6 * * 1 /bin/weekly.sh")
    assert entry.schedule_expression() == "30 6 * * 1"


def test_parse_crontab_skips_invalid_with_warning():
    text = "* * * bad_entry\n0 0 * * * /valid.sh"
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        entries = parse_crontab(text)
        assert len(entries) == 1
        assert len(w) == 1
