"""Retry policy configuration and evaluation for cron job alerts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class RetryPolicyError(Exception):
    """Raised when a retry policy is misconfigured."""


@dataclass
class RetryPolicy:
    """Defines how many times and how often a failed alert should be retried."""

    max_attempts: int = 3
    interval_seconds: int = 60
    ignore_commands: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise RetryPolicyError("max_attempts must be >= 1")
        if self.interval_seconds < 1:
            raise RetryPolicyError("interval_seconds must be >= 1")


@dataclass
class RetryState:
    """Tracks retry attempts for a single alert key."""

    attempts: int = 0
    last_attempt: Optional[datetime] = None


def should_retry(state: RetryState, policy: RetryPolicy, now: Optional[datetime] = None) -> bool:
    """Return True if another attempt is allowed under *policy* given *state*."""
    if state.attempts >= policy.max_attempts:
        return False
    if state.last_attempt is None:
        return True
    now = now or datetime.utcnow()
    elapsed = (now - state.last_attempt).total_seconds()
    return elapsed >= policy.interval_seconds


def record_attempt(state: RetryState, now: Optional[datetime] = None) -> RetryState:
    """Return a new *RetryState* with the attempt counter incremented."""
    return RetryState(
        attempts=state.attempts + 1,
        last_attempt=now or datetime.utcnow(),
    )


def build_retry_registry() -> Dict[str, RetryState]:
    """Return an empty registry mapping alert-key -> RetryState."""
    return {}
