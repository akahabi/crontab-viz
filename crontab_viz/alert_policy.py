"""Alert policy: decides when to fire notifications based on conflict severity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Tuple

from crontab_viz.scheduler import ScheduledRun


@dataclass
class AlertPolicy:
    """Controls which conflicts trigger notifications.

    Attributes:
        min_conflicts: Minimum number of conflict pairs before alerting.
        ignored_commands: Commands to exclude from conflict alerting.
        cooldown: Minimum time between repeated alerts for the same pair.
    """
    min_conflicts: int = 1
    ignored_commands: List[str] = field(default_factory=list)
    cooldown: timedelta = timedelta(minutes=60)


def filter_conflicts(
    conflicts: List[Tuple[ScheduledRun, ScheduledRun]],
    policy: AlertPolicy,
) -> List[Tuple[ScheduledRun, ScheduledRun]]:
    """Return only the conflicts that satisfy *policy*.

    Args:
        conflicts: All detected conflict pairs.
        policy: The active AlertPolicy.

    Returns:
        Filtered list of conflict pairs that should trigger an alert.
    """
    filtered = [
        (a, b)
        for a, b in conflicts
        if a.entry.command not in policy.ignored_commands
        and b.entry.command not in policy.ignored_commands
    ]
    return filtered


def should_alert(
    conflicts: List[Tuple[ScheduledRun, ScheduledRun]],
    policy: AlertPolicy,
) -> bool:
    """Return True when the conflict list warrants sending an alert.

    Args:
        conflicts: Pre-filtered conflict pairs.
        policy: The active AlertPolicy.
    """
    return len(conflicts) >= policy.min_conflicts


def build_alert_subject(conflicts: List[Tuple[ScheduledRun, ScheduledRun]]) -> str:
    """Return a concise e-mail subject for the given conflicts."""
    n = len(conflicts)
    noun = "conflict" if n == 1 else "conflicts"
    return f"[crontab-viz] {n} cron job {noun} detected"
