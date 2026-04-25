"""Configuration dataclass for the overlap detector."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


class OverlapConfigError(Exception):
    """Raised for invalid overlap configuration values."""


@dataclass
class OverlapConfig:
    """Settings that control how overlaps are detected.

    Attributes:
        duration_seconds: Assumed job duration used to define each run's window.
        ignored_commands: Commands excluded from overlap analysis.
        min_overlap_seconds: Overlaps shorter than this threshold are suppressed.
    """

    duration_seconds: float = 60.0
    ignored_commands: List[str] = field(default_factory=list)
    min_overlap_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise OverlapConfigError("duration_seconds must be > 0")
        if self.min_overlap_seconds < 0:
            raise OverlapConfigError("min_overlap_seconds must be >= 0")

    def is_ignored(self, command: str) -> bool:
        """Return True if *command* should be skipped during overlap analysis."""
        return command in self.ignored_commands

    def passes_threshold(self, overlap_seconds: float) -> bool:
        """Return True if the overlap duration meets the minimum threshold."""
        return overlap_seconds >= self.min_overlap_seconds
