"""Summarise and format run history for display."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import List, Optional

from crontab_viz.history import RunRecord


def most_frequent_commands(records: List[RunRecord], top_n: int = 5) -> List[tuple]:
    """Return the *top_n* most-recorded commands as (command, count) pairs."""
    counter: Counter = Counter(r.command for r in records)
    return counter.most_common(top_n)


def records_for_command(records: List[RunRecord], command: str) -> List[RunRecord]:
    """Filter *records* to those matching *command* exactly."""
    return [r for r in records if r.command == command]


def format_history_table(records: List[RunRecord], limit: int = 20) -> str:
    """Render the most-recent *limit* records as a plain-text table."""
    recent = records[-limit:] if len(records) > limit else records
    if not recent:
        return "No history records found."

    header = f"{'COMMAND':<40} {'SCHEDULED AT':<22} {'RECORDED AT':<22}"
    separator = "-" * len(header)
    lines = [header, separator]
    for rec in reversed(recent):
        cmd = rec.command[:38] + ".." if len(rec.command) > 40 else rec.command
        lines.append(f"{cmd:<40} {rec.scheduled_at:<22} {rec.recorded_at:<22}")
    return "\n".join(lines)


def summarise_history(records: List[RunRecord]) -> str:
    """Return a short human-readable summary string."""
    if not records:
        return "History is empty."
    total = len(records)
    unique = len({r.command for r in records})
    first = records[0].scheduled_at
    last = records[-1].scheduled_at
    return (
        f"{total} record(s) for {unique} unique command(s). "
        f"Earliest: {first}  Latest: {last}"
    )
