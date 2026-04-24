"""Crontab file loading and system crontab discovery."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Optional

from crontab_viz.parser import CronEntry, CronParseError, parse_line


class CrontabLoadError(Exception):
    """Raised when a crontab file cannot be loaded or parsed."""


def load_file(path: str | Path) -> List[CronEntry]:
    """Parse all valid cron entries from a crontab file.

    Args:
        path: Path to the crontab file.

    Returns:
        List of successfully parsed CronEntry objects.

    Raises:
        CrontabLoadError: If the file cannot be read.
    """
    path = Path(path)
    if not path.exists():
        raise CrontabLoadError(f"File not found: {path}")
    if not path.is_file():
        raise CrontabLoadError(f"Not a file: {path}")

    entries: List[CronEntry] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CrontabLoadError(f"Cannot read {path}: {exc}") from exc

    for lineno, line in enumerate(lines, start=1):
        try:
            entry = parse_line(line)
            if entry is not None:
                entries.append(entry)
        except CronParseError:
            # Skip malformed lines silently; callers can log if needed
            pass

    return entries


def load_user_crontab(user: Optional[str] = None) -> List[CronEntry]:
    """Load the crontab for the current (or specified) user via `crontab -l`.

    Args:
        user: Optional username; if None uses the current user.

    Returns:
        List of successfully parsed CronEntry objects.

    Raises:
        CrontabLoadError: If the crontab command fails.
    """
    cmd = ["crontab", "-l"]
    if user:
        cmd += ["-u", user]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise CrontabLoadError(f"crontab command failed: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise CrontabLoadError(f"crontab -l returned {result.returncode}: {stderr}")

    entries: List[CronEntry] = []
    for line in result.stdout.splitlines():
        try:
            entry = parse_line(line)
            if entry is not None:
                entries.append(entry)
        except CronParseError:
            pass

    return entries
