"""Command-line interface for crontab-viz."""

import argparse
import sys
from datetime import datetime
from typing import Optional

from rich.console import Console

from crontab_viz.dashboard import build_layout, run_dashboard
from crontab_viz.loader import CrontabLoadError, load_file, load_user_crontab
from crontab_viz.scheduler import detect_conflicts, schedule_all
from crontab_viz.formatter import format_conflicts, format_schedule_table, format_summary

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-viz",
        description="Visualize crontab schedules in the terminal.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help="Path to a crontab file (defaults to current user's crontab).",
    )
    parser.add_argument(
        "-n",
        "--next",
        type=int,
        default=5,
        metavar="N",
        help="Number of upcoming runs to show per job (default: 5).",
    )
    parser.add_argument(
        "--no-watch",
        action="store_true",
        help="Disable file-change watching (single snapshot).",
    )
    parser.add_argument(
        "--conflicts-window",
        type=int,
        default=60,
        metavar="MINUTES",
        help="Minutes ahead to scan for job conflicts (default: 60).",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Print a one-shot table and exit (no live dashboard).",
    )
    return parser


def snapshot_mode(
    path: Optional[str],
    n: int,
    window_minutes: int,
) -> None:
    """Print schedule table once and exit."""
    try:
        entries = load_file(path) if path else load_user_crontab()
    except CrontabLoadError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    now = datetime.now()
    runs = schedule_all(entries, now=now, n=n)
    conflicts = detect_conflicts(entries, now=now, window_minutes=window_minutes)

    console.print(format_schedule_table(runs))
    console.print(format_conflicts(conflicts))
    console.print(format_summary(entries, runs))


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.snapshot:
        snapshot_mode(args.file, args.next, args.conflicts_window)
        return

    try:
        run_dashboard(
            path=args.file,
            n=args.next,
            watch=not args.no_watch,
        )
    except CrontabLoadError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
