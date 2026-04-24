"""Conflict and schedule notification system for crontab-viz."""
from __future__ import annotations

import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Callable, List, Optional

from crontab_viz.scheduler import ScheduledRun


@dataclass
class NotificationConfig:
    """Configuration for the notifier."""
    smtp_host: str = "localhost"
    smtp_port: int = 25
    sender: str = "crontab-viz@localhost"
    recipients: List[str] = field(default_factory=list)
    use_tls: bool = False
    username: Optional[str] = None
    password: Optional[str] = None


class NotificationError(Exception):
    """Raised when a notification cannot be sent."""


def build_conflict_message(
    conflicts: List[tuple[ScheduledRun, ScheduledRun]],
) -> str:
    """Return a human-readable string describing detected conflicts."""
    if not conflicts:
        return "No conflicts detected."
    lines = [f"Detected {len(conflicts)} cron conflict(s):\n"]
    for a, b in conflicts:
        lines.append(
            f"  - '{a.entry.command}' and '{b.entry.command}' "
            f"overlap at {a.run_time.isoformat()}"
        )
    return "\n".join(lines)


def send_notification(
    config: NotificationConfig,
    subject: str,
    body: str,
    *,
    smtp_factory: Optional[Callable[..., smtplib.SMTP]] = None,
) -> None:
    """Send an e-mail notification via SMTP.

    Args:
        config: SMTP and addressing configuration.
        subject: E-mail subject line.
        body: Plain-text body.
        smtp_factory: Optional injectable SMTP constructor (for testing).

    Raises:
        NotificationError: If the message cannot be delivered.
    """
    if not config.recipients:
        raise NotificationError("No recipients configured.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.sender
    msg["To"] = ", ".join(config.recipients)
    msg.set_content(body)

    factory = smtp_factory or smtplib.SMTP
    try:
        with factory(config.smtp_host, config.smtp_port) as server:
            if config.use_tls:
                server.starttls()
            if config.username and config.password:
                server.login(config.username, config.password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        raise NotificationError(f"Failed to send notification: {exc}") from exc
