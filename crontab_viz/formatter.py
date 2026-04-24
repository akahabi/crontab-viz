"""Formatting utilities for crontab schedule output in the terminal dashboard."""

from datetime import datetime
from typing import List, Tuple

from crontab_viz.scheduler import ConflictGroup, ScheduledRun

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
CYAN = "\033[36m"
DIM = "\033[2m"

TIME_FMT = "%Y-%m-%d %H:%M"


def format_run(run: ScheduledRun, now: datetime | None = None) -> str:
    """Format a single scheduled run as a human-readable line."""
    if now is None:
        now = datetime.now()
    delta = run.run_at - now
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        relative = f"{total_seconds}s"
    elif total_seconds < 3600:
        relative = f"{total_seconds // 60}m"
    else:
        relative = f"{total_seconds // 3600}h {(total_seconds % 3600) // 60}m"

    time_str = run.run_at.strftime(TIME_FMT)
    return f"{CYAN}{time_str}{RESET}  (in {relative:<8})  {run.entry.command}"


def format_schedule_table(runs: List[ScheduledRun], now: datetime | None = None) -> str:
    """Format a list of scheduled runs as a sorted table."""
    if not runs:
        return f"{DIM}No upcoming runs found.{RESET}"
    if now is None:
        now = datetime.now()
    sorted_runs = sorted(runs, key=lambda r: r.run_at)
    header = f"{BOLD}{'SCHEDULED AT':<18}  {'IN':<10}  COMMAND{RESET}"
    separator = "-" * 60
    lines = [header, separator]
    for run in sorted_runs:
        lines.append(format_run(run, now))
    return "\n".join(lines)


def format_conflicts(conflicts: List[ConflictGroup]) -> str:
    """Format detected conflicts with highlighted warnings."""
    if not conflicts:
        return f"{GREEN}No conflicts detected.{RESET}"
    lines = [f"{RED}{BOLD}⚠  Conflicts Detected{RESET}"]
    for group in conflicts:
        time_str = group.run_at.strftime(TIME_FMT)
        lines.append(f"\n  {YELLOW}{time_str}{RESET} — {len(group.entries)} jobs overlap:")
        for entry in group.entries:
            lines.append(f"    {DIM}•{RESET} {entry.command}  {DIM}[{entry.schedule_expression}]{RESET}")
    return "\n".join(lines)


def format_summary(total_entries: int, total_runs: int, conflict_count: int) -> str:
    """Render a one-line summary bar."""
    conflict_part = (
        f"{RED}{conflict_count} conflict(s){RESET}"
        if conflict_count
        else f"{GREEN}0 conflicts{RESET}"
    )
    return (
        f"{BOLD}Entries:{RESET} {total_entries}  "
        f"{BOLD}Upcoming runs:{RESET} {total_runs}  "
        f"{BOLD}Conflicts:{RESET} {conflict_part}"
    )
