"""Tests for the CLI entry point."""

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from crontab_viz.cli import build_parser, main, snapshot_mode
from crontab_viz.parser import CronEntry


def make_entry(command: str) -> CronEntry:
    return CronEntry(
        schedule="*/10 * * * *",
        command=command,
        raw=f"*/10 * * * * {command}",
    )


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.next == 5
    assert args.conflicts_window == 60
    assert args.snapshot is False
    assert args.no_watch is False


def test_build_parser_custom_n():
    parser = build_parser()
    args = parser.parse_args(["-n", "10"])
    assert args.next == 10


def test_build_parser_file_positional():
    parser = build_parser()
    args = parser.parse_args(["/etc/crontab"])
    assert args.file == "/etc/crontab"


def test_snapshot_mode_prints_output(tmp_path, capsys):
    cron_file = tmp_path / "crontab"
    cron_file.write_text("*/5 * * * * echo hello\n")

    with patch("crontab_viz.cli.console") as mock_console:
        snapshot_mode(str(cron_file), n=2, window_minutes=60)
        assert mock_console.print.called


def test_snapshot_mode_missing_file_exits():
    with pytest.raises(SystemExit) as exc_info:
        with patch("crontab_viz.cli.console"):
            snapshot_mode("/nonexistent/crontab", n=2, window_minutes=60)
    assert exc_info.value.code == 1


def test_main_snapshot_flag(tmp_path):
    cron_file = tmp_path / "crontab"
    cron_file.write_text("0 2 * * * backup.sh\n")

    with patch("crontab_viz.cli.console"):
        main([str(cron_file), "--snapshot", "-n", "3"])


def test_main_load_error_exits():
    with patch("crontab_viz.cli.load_user_crontab") as mock_load:
        from crontab_viz.loader import CrontabLoadError

        mock_load.side_effect = CrontabLoadError("no crontab")
        with patch("crontab_viz.cli.console"):
            with pytest.raises(SystemExit) as exc_info:
                main(["--snapshot"])
        assert exc_info.value.code == 1
