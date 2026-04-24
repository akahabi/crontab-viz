"""Rate-limiting / throttle logic for cron job execution tracking.

Prevents a single command from being counted or alerted more than
`max_per_window` times within a rolling `window_seconds` period.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict


class RunLimiterError(ValueError):
    """Raised when RunLimiter is configured with invalid parameters."""


@dataclass
class RunLimiter:
    """Sliding-window rate limiter keyed by command string.

    Parameters
    ----------
    window_seconds:
        Length of the rolling window in seconds (must be > 0).
    max_per_window:
        Maximum number of allowed occurrences within the window (must be >= 1).
    """

    window_seconds: float = 3600.0
    max_per_window: int = 10
    _timestamps: Dict[str, Deque[float]] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise RunLimiterError("window_seconds must be positive")
        if self.max_per_window < 1:
            raise RunLimiterError("max_per_window must be at least 1")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_allowed(self, command: str, now: float | None = None) -> bool:
        """Return True if *command* is within its rate limit at *now*.

        Calling this method does **not** record the event; call
        :meth:`record` to register an occurrence.
        """
        now = now if now is not None else time.time()
        self._evict(command, now)
        bucket = self._timestamps.get(command, deque())
        return len(bucket) < self.max_per_window

    def record(self, command: str, now: float | None = None) -> None:
        """Record one occurrence of *command* at *now*."""
        now = now if now is not None else time.time()
        self._evict(command, now)
        if command not in self._timestamps:
            self._timestamps[command] = deque()
        self._timestamps[command].append(now)

    def count(self, command: str, now: float | None = None) -> int:
        """Return the number of recorded occurrences still within the window."""
        now = now if now is not None else time.time()
        self._evict(command, now)
        return len(self._timestamps.get(command, deque()))

    def reset(self, command: str | None = None) -> None:
        """Clear recorded timestamps for *command*, or all commands if None."""
        if command is None:
            self._timestamps.clear()
        else:
            self._timestamps.pop(command, None)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict(self, command: str, now: float) -> None:
        """Remove timestamps older than the rolling window for *command*."""
        bucket = self._timestamps.get(command)
        if not bucket:
            return
        cutoff = now - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if not bucket:
            del self._timestamps[command]
