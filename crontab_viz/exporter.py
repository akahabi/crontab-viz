"""Export crontab schedule data to JSON or CSV formats."""

from __future__ import annotations

import csv
import json
import io
from datetime import datetime
from typing import List, Optional

from crontab_viz.scheduler import ScheduledRun


class ExportError(Exception):
    """Raised when export fails."""


def runs_to_dicts(runs: List[ScheduledRun]) -> List[dict]:
    """Convert a list of ScheduledRun objects to plain dicts."""
    return [
        {
            "command": run.entry.command,
            "schedule": run.entry.schedule_expression,
            "next_run": run.run_time.isoformat(),
            "relative_seconds": int(
                (run.run_time - datetime.now()).total_seconds()
            ),
        }
        for run in runs
    ]


def export_json(
    runs: List[ScheduledRun],
    *,
    indent: int = 2,
    fp: Optional[io.TextIOBase] = None,
) -> str:
    """Serialize scheduled runs to a JSON string.

    If *fp* is provided the result is also written to that file-like object.
    Returns the JSON string in all cases.
    """
    data = runs_to_dicts(runs)
    text = json.dumps(data, indent=indent)
    if fp is not None:
        fp.write(text)
    return text


def export_csv(
    runs: List[ScheduledRun],
    *,
    fp: Optional[io.TextIOBase] = None,
) -> str:
    """Serialize scheduled runs to a CSV string.

    If *fp* is provided the result is also written to that file-like object.
    Returns the CSV string in all cases.
    """
    buf = io.StringIO()
    fieldnames = ["command", "schedule", "next_run", "relative_seconds"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(runs_to_dicts(runs))
    text = buf.getvalue()
    if fp is not None:
        fp.write(text)
    return text
