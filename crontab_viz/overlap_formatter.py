"""Format overlap detection results for terminal display."""
from __future__ import annotations

from typing import List

from crontab_viz.overlap_detector import OverlapWindow, group_by_minute

_HEADER = "Temporal Overlaps"
_SEP = "-" * 60


def format_overlap_row(ow: OverlapWindow) -> str:
    """Single-line summary of one overlap window."""
    time_str = ow.run_a.run_time.strftime("%Y-%m-%d %H:%M")
    return (
        f"  {time_str}  "
        f"{ow.run_a.entry.command!r:30s} <-> "
        f"{ow.run_b.entry.command!r:30s} "
        f"(+{ow.overlap_seconds:.0f}s)"
    )


def format_overlap_table(overlaps: List[OverlapWindow]) -> str:
    """Render a full table of overlaps grouped by minute."""
    if not overlaps:
        return f"{_HEADER}\n{_SEP}\n  No overlaps detected.\n"

    lines: List[str] = [_HEADER, _SEP]
    groups = group_by_minute(overlaps)
    for minute_key, group in sorted(groups.items()):
        lines.append(f"  [{minute_key}]")
        for ow in group:
            lines.append(format_overlap_row(ow))
    lines.append(_SEP)
    lines.append(f"  Total overlapping pairs: {len(overlaps)}")
    return "\n".join(lines) + "\n"


def format_overlap_summary(overlaps: List[OverlapWindow]) -> str:
    """One-line summary suitable for a status bar."""
    if not overlaps:
        return "Overlaps: none"
    commands = {ow.run_a.entry.command for ow in overlaps} | {
        ow.run_b.entry.command for ow in overlaps
    }
    return f"Overlaps: {len(overlaps)} pair(s) across {len(commands)} command(s)"
