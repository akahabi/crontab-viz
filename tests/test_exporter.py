"""Tests for crontab_viz.exporter."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from crontab_viz.exporter import export_csv, export_json, runs_to_dicts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run(command: str, minutes_ahead: int = 10):
    entry = MagicMock()
    entry.command = command
    entry.schedule_expression = "* * * * *"
    run = MagicMock()
    run.entry = entry
    run.run_time = datetime.now() + timedelta(minutes=minutes_ahead)
    return run


# ---------------------------------------------------------------------------
# runs_to_dicts
# ---------------------------------------------------------------------------

def test_runs_to_dicts_keys():
    runs = [_make_run("echo hello")]
    result = runs_to_dicts(runs)
    assert len(result) == 1
    assert set(result[0].keys()) == {"command", "schedule", "next_run", "relative_seconds"}


def test_runs_to_dicts_command_value():
    runs = [_make_run("backup.sh")]
    assert runs_to_dicts(runs)[0]["command"] == "backup.sh"


def test_runs_to_dicts_relative_seconds_positive():
    runs = [_make_run("job", minutes_ahead=5)]
    secs = runs_to_dicts(runs)[0]["relative_seconds"]
    assert secs > 0


# ---------------------------------------------------------------------------
# export_json
# ---------------------------------------------------------------------------

def test_export_json_returns_valid_json():
    runs = [_make_run("echo 1"), _make_run("echo 2")]
    text = export_json(runs)
    parsed = json.loads(text)
    assert len(parsed) == 2


def test_export_json_writes_to_fp():
    runs = [_make_run("echo test")]
    buf = io.StringIO()
    export_json(runs, fp=buf)
    buf.seek(0)
    assert json.loads(buf.read())[0]["command"] == "echo test"


def test_export_json_empty_list():
    text = export_json([])
    assert json.loads(text) == []


# ---------------------------------------------------------------------------
# export_csv
# ---------------------------------------------------------------------------

def test_export_csv_returns_string_with_header():
    runs = [_make_run("cron_job")]
    text = export_csv(runs)
    assert "command" in text
    assert "next_run" in text


def test_export_csv_contains_command():
    runs = [_make_run("my_script.sh")]
    text = export_csv(runs)
    assert "my_script.sh" in text


def test_export_csv_writes_to_fp():
    runs = [_make_run("fp_test")]
    buf = io.StringIO()
    export_csv(runs, fp=buf)
    buf.seek(0)
    reader = csv.DictReader(buf)
    rows = list(reader)
    assert rows[0]["command"] == "fp_test"


def test_export_csv_row_count():
    runs = [_make_run(f"job{i}") for i in range(4)]
    text = export_csv(runs)
    lines = [l for l in text.strip().splitlines() if l]
    # header + 4 data rows
    assert len(lines) == 5
