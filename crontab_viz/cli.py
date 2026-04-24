"""Command-line interface for crontab-viz."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from crontab_viz.formatter import format_conflicts, format_schedule_table, format_summary
from crontab_viz.loader import CrontabLoadError, load_file, load_user_crontab
from crontab_viz.scheduler import detect_conflicts, schedule_all
from crontab_viz.exporter import export_csv, export_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-viz",
        description="Visualize upcoming cron job schedules.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a crontab file (defaults to current user's crontab).",
    )
    parser.add_argument(
        "-n",
        type=int,
        default=5,
        dest="n",
        help="Number of upcoming runs to show per job (default: 5).",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Print a one-shot snapshot and exit (no live dashboard).",
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv"],
        default=None,
        help="Export the upcoming schedule to stdout in JSON or CSV format.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write --export output to FILE instead of stdout.",
    )
    return parser


def snapshot_mode(entries, n: int = 5) -> str:
    runs = schedule_all(entries, n=n)
    conflicts = detect_conflicts(runs)
    lines: List[str] = []
    lines.append(format_schedule_table(runs))
    if conflicts:
        lines.append(format_conflicts(conflicts))
    lines.append(format_summary(runs, conflicts))
    return "\n".join(lines)


def _export_mode(entries, fmt: str, n: int, output: Optional[str]) -> None:
    runs = schedule_all(entries, n=n)
    if fmt == "json":
        if output:
            with open(output, "w") as fp:
                export_json(runs, fp=fp)
        else:
            print(export_json(runs))
    else:
        if output:
            with open(output, "w") as fp:
                export_csv(runs, fp=fp)
        else:
            print(export_csv(runs), end="")


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        entries = load_file(args.file) if args.file else load_user_crontab()
    except CrontabLoadError as exc:
        print(f"Error loading crontab: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.export:
        _export_mode(entries, args.export, args.n, args.output)
        return

    if args.snapshot:
        print(snapshot_mode(entries, n=args.n))
        return

    from crontab_viz.dashboard import run_dashboard
    run_dashboard(entries, n=args.n)


if __name__ == "__main__":  # pragma: no cover
    main()
