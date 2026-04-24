"""Orchestrates conflict alerting with retry-policy enforcement."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from crontab_viz.alert_policy import AlertPolicy, filter_conflicts, should_alert
from crontab_viz.notifier import NotificationConfig, build_conflict_message, send_notification
from crontab_viz.retry_policy import (
    RetryPolicy,
    RetryState,
    build_retry_registry,
    record_attempt,
    should_retry,
)
from crontab_viz.scheduler import ScheduledRun


def _conflict_key(runs: List[ScheduledRun]) -> str:
    """Stable key representing a set of conflicting runs."""
    commands = sorted(r.entry.command for r in runs)
    return "|".join(commands)


class AlertRunner:
    """Sends conflict notifications while respecting retry and alert policies."""

    def __init__(
        self,
        notification_config: NotificationConfig,
        alert_policy: Optional[AlertPolicy] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ) -> None:
        self._notif_cfg = notification_config
        self._alert_policy = alert_policy or AlertPolicy()
        self._retry_policy = retry_policy or RetryPolicy()
        self._registry: Dict[str, RetryState] = build_retry_registry()

    # ------------------------------------------------------------------
    def process_conflicts(
        self,
        conflicts: List[List[ScheduledRun]],
        now: Optional[datetime] = None,
    ) -> int:
        """Evaluate *conflicts*, send alerts where due, return number sent."""
        now = now or datetime.utcnow()
        filtered = filter_conflicts(conflicts, self._alert_policy)
        sent = 0
        for group in filtered:
            if not should_alert(group, self._alert_policy):
                continue
            key = _conflict_key(group)
            state = self._registry.get(key, RetryState())
            if not should_retry(state, self._retry_policy, now=now):
                continue
            message = build_conflict_message(group)
            send_notification(message, self._notif_cfg)
            self._registry[key] = record_attempt(state, now=now)
            sent += 1
        return sent

    def reset(self) -> None:
        """Clear all retry state (e.g. after a crontab reload)."""
        self._registry = build_retry_registry()
