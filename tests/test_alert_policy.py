"""Tests for crontab_viz.alert_policy."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from crontab_viz.alert_policy import (
    AlertPolicy,
    build_alert_subject,
    filter_conflicts,
    should_alert,
)
from crontab_viz.parser import CronEntry
from crontab_viz.scheduler import ScheduledRun


def _run(command: str) -> ScheduledRun:
    entry = CronEntry(
        schedule_expression="*/5 * * * *",
        command=command,
        raw_line=f"*/5 * * * * {command}",
    )
    return ScheduledRun(
        entry=entry,
        run_time=datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc),
    )


def test_filter_conflicts_empty():
    assert filter_conflicts([], AlertPolicy()) == []


def test_filter_conflicts_removes_ignored():
    policy = AlertPolicy(ignored_commands=["backup.sh"])
    pairs = [(_run("backup.sh"), _run("report.py"))]
    assert filter_conflicts(pairs, policy) == []


def test_filter_conflicts_keeps_non_ignored():
    policy = AlertPolicy(ignored_commands=["other.sh"])
    pairs = [(_run("a.sh"), _run("b.sh"))]
    assert len(filter_conflicts(pairs, policy)) == 1


def test_filter_conflicts_both_must_pass():
    policy = AlertPolicy(ignored_commands=["b.sh"])
    pairs = [(_run("a.sh"), _run("b.sh")), (_run("c.sh"), _run("d.sh"))]
    result = filter_conflicts(pairs, policy)
    assert len(result) == 1
    assert result[0][0].entry.command == "c.sh"


def test_should_alert_false_when_below_min():
    policy = AlertPolicy(min_conflicts=3)
    pairs = [(_run("a"), _run("b")), (_run("c"), _run("d"))]
    assert should_alert(pairs, policy) is False


def test_should_alert_true_when_at_min():
    policy = AlertPolicy(min_conflicts=2)
    pairs = [(_run("a"), _run("b")), (_run("c"), _run("d"))]
    assert should_alert(pairs, policy) is True


def test_should_alert_true_when_above_min():
    policy = AlertPolicy(min_conflicts=1)
    pairs = [(_run("a"), _run("b")), (_run("c"), _run("d"))]
    assert should_alert(pairs, policy) is True


def test_build_alert_subject_singular():
    subject = build_alert_subject([(_run("a"), _run("b"))])
    assert "1" in subject
    assert "conflict" in subject.lower()
    assert "conflicts" not in subject.lower()


def test_build_alert_subject_plural():
    pairs = [(_run("a"), _run("b")), (_run("c"), _run("d"))]
    subject = build_alert_subject(pairs)
    assert "2" in subject
    assert "conflicts" in subject.lower()


def test_build_alert_subject_prefix():
    subject = build_alert_subject([(_run("x"), _run("y"))])
    assert subject.startswith("[crontab-viz]")
