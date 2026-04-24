"""Tests for crontab_viz.notifier."""
from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest

from crontab_viz.notifier import (
    NotificationConfig,
    NotificationError,
    build_conflict_message,
    send_notification,
)
from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import ScheduledRun


def _make_run(command: str, dt: datetime | None = None) -> ScheduledRun:
    entry = CronEntry(
        schedule_expression="* * * * *",
        command=command,
        raw_line=f"* * * * * {command}",
    )
    return ScheduledRun(
        entry=entry,
        run_time=dt or datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
    )


def test_build_conflict_message_no_conflicts():
    msg = build_conflict_message([])
    assert "No conflicts" in msg


def test_build_conflict_message_lists_commands():
    a = _make_run("backup.sh")
    b = _make_run("report.py")
    msg = build_conflict_message([(a, b)])
    assert "backup.sh" in msg
    assert "report.py" in msg


def test_build_conflict_message_count():
    pairs = [(_make_run("a"), _make_run("b")), (_make_run("c"), _make_run("d"))]
    msg = build_conflict_message(pairs)
    assert "2" in msg


def test_send_notification_no_recipients_raises():
    cfg = NotificationConfig(recipients=[])
    with pytest.raises(NotificationError, match="No recipients"):
        send_notification(cfg, "Subject", "Body")


def test_send_notification_calls_smtp(monkeypatch):
    cfg = NotificationConfig(recipients=["ops@example.com"])
    mock_server = MagicMock()
    mock_server.__enter__ = lambda s: s
    mock_server.__exit__ = MagicMock(return_value=False)
    factory = MagicMock(return_value=mock_server)

    send_notification(cfg, "Test", "Hello", smtp_factory=factory)

    factory.assert_called_once_with(cfg.smtp_host, cfg.smtp_port)
    mock_server.send_message.assert_called_once()


def test_send_notification_uses_tls(monkeypatch):
    cfg = NotificationConfig(recipients=["a@b.com"], use_tls=True)
    mock_server = MagicMock()
    mock_server.__enter__ = lambda s: s
    mock_server.__exit__ = MagicMock(return_value=False)
    factory = MagicMock(return_value=mock_server)

    send_notification(cfg, "S", "B", smtp_factory=factory)

    mock_server.starttls.assert_called_once()


def test_send_notification_smtp_error_raises():
    cfg = NotificationConfig(recipients=["a@b.com"])

    def bad_factory(host, port):
        raise OSError("connection refused")

    with pytest.raises(NotificationError, match="Failed to send"):
        send_notification(cfg, "S", "B", smtp_factory=bad_factory)


def test_send_notification_subject_and_body():
    cfg = NotificationConfig(recipients=["ops@example.com"])
    captured: list[EmailMessage] = []
    mock_server = MagicMock()
    mock_server.__enter__ = lambda s: s
    mock_server.__exit__ = MagicMock(return_value=False)
    mock_server.send_message.side_effect = lambda m: captured.append(m)
    factory = MagicMock(return_value=mock_server)

    send_notification(cfg, "Alert", "Something happened", smtp_factory=factory)

    assert captured[0]["Subject"] == "Alert"
    assert "Something happened" in captured[0].get_content()
