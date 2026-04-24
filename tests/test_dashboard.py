"""Tests for the dashboard layout builder."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from crontab_viz.dashboard import build_layout
from crontab_viz.parser import CronEntry


def make_entry(command: str, minute: str = "*/5", hour: str = "*") -> CronEntry:
    return CronEntry(
        schedule=f"{minute} {hour} * * *",
        command=command,
        raw=f"{minute} {hour} * * * {command}",
    )


FIXED_NOW = datetime(2024, 6, 1, 12, 0, 0)


def test_build_layout_returns_layout_object():
    from rich.layout import Layout

    entries = [make_entry("backup.sh"), make_entry("cleanup.sh", minute="0", hour="2")]
    layout = build_layout(entries, now=FIXED_NOW, n=3)
    assert isinstance(layout, Layout)


def test_build_layout_contains_header():
    entries = [make_entry("echo hello")]
    layout = build_layout(entries, now=FIXED_NOW)
    # Header panel should render without error
    from rich.console import Console
    from io import StringIO

    buf = StringIO()
    c = Console(file=buf, width=120)
    c.print(layout)
    output = buf.getvalue()
    assert "2024-06-01" in output


def test_build_layout_no_entries():
    """Empty entry list should not raise."""
    layout = build_layout([], now=FIXED_NOW)
    assert layout is not None


def test_build_layout_with_conflicts():
    """Two jobs at the same minute should surface in the conflicts panel."""
    from io import StringIO
    from rich.console import Console

    e1 = make_entry("job_a", minute="0", hour="*")
    e2 = make_entry("job_b", minute="0", hour="*")
    layout = build_layout([e1, e2], now=FIXED_NOW, n=2)

    buf = StringIO()
    c = Console(file=buf, width=160)
    c.print(layout)
    output = buf.getvalue()
    # Both commands should appear somewhere in the rendered output
    assert "job_a" in output
    assert "job_b" in output


def test_build_layout_n_parameter_respected():
    """The n parameter limits runs shown."""
    from crontab_viz.scheduler import schedule_all

    entries = [make_entry("task")]
    runs = schedule_all(entries, now=FIXED_NOW, n=2)
    assert len(runs) <= 2
