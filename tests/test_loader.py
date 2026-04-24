"""Tests for crontab_viz.loader."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from crontab_viz.loader import CrontabLoadError, load_file, load_user_crontab


SAMPLE_CRONTAB = textwrap.dedent("""\
    # Daily backup
    0 2 * * * /usr/bin/backup.sh
    # Hourly cleanup
    0 * * * * /usr/bin/cleanup.sh
    @reboot /usr/bin/startup.sh
""")


def test_load_file_returns_entries(tmp_path: Path) -> None:
    crontab = tmp_path / "crontab"
    crontab.write_text(SAMPLE_CRONTAB, encoding="utf-8")
    entries = load_file(crontab)
    assert len(entries) == 3


def test_load_file_commands(tmp_path: Path) -> None:
    crontab = tmp_path / "crontab"
    crontab.write_text(SAMPLE_CRONTAB, encoding="utf-8")
    commands = [e.command for e in load_file(crontab)]
    assert "/usr/bin/backup.sh" in commands
    assert "/usr/bin/cleanup.sh" in commands


def test_load_file_skips_comments(tmp_path: Path) -> None:
    content = "# just a comment\n5 4 * * 0 /weekly.sh\n"
    crontab = tmp_path / "crontab"
    crontab.write_text(content, encoding="utf-8")
    entries = load_file(crontab)
    assert len(entries) == 1
    assert entries[0].command == "/weekly.sh"


def test_load_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(CrontabLoadError, match="not found"):
        load_file(tmp_path / "nonexistent")


def test_load_file_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(CrontabLoadError, match="Not a file"):
        load_file(tmp_path)


def test_load_file_skips_malformed_lines(tmp_path: Path) -> None:
    content = "not a valid cron line\n0 0 * * * /valid.sh\n"
    crontab = tmp_path / "crontab"
    crontab.write_text(content, encoding="utf-8")
    entries = load_file(crontab)
    assert len(entries) == 1


def test_load_user_crontab_success() -> None:
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "*/5 * * * * /ping.sh\n"
    with patch("crontab_viz.loader.subprocess.run", return_value=mock_result):
        entries = load_user_crontab()
    assert len(entries) == 1
    assert entries[0].command == "/ping.sh"


def test_load_user_crontab_nonzero_raises() -> None:
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "no crontab for user"
    with patch("crontab_viz.loader.subprocess.run", return_value=mock_result):
        with pytest.raises(CrontabLoadError, match="returned 1"):
            load_user_crontab()


def test_load_user_crontab_command_not_found_raises() -> None:
    with patch(
        "crontab_viz.loader.subprocess.run", side_effect=FileNotFoundError
    ):
        with pytest.raises(CrontabLoadError, match="command failed"):
            load_user_crontab()
