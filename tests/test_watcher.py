"""Tests for crontab_viz.watcher."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from crontab_viz.watcher import CrontabWatcher


SAMPLE = "0 * * * * /hourly.sh\n"


def test_check_triggers_callback_on_first_call(tmp_path: Path) -> None:
    crontab = tmp_path / "crontab"
    crontab.write_text(SAMPLE, encoding="utf-8")
    callback = MagicMock()
    watcher = CrontabWatcher(crontab, callback)
    changed = watcher.check()
    assert changed is True
    callback.assert_called_once()
    entries = callback.call_args[0][0]
    assert len(entries) == 1


def test_check_no_change_does_not_call_callback(tmp_path: Path) -> None:
    crontab = tmp_path / "crontab"
    crontab.write_text(SAMPLE, encoding="utf-8")
    callback = MagicMock()
    watcher = CrontabWatcher(crontab, callback)
    watcher.check()  # first call — sets mtime
    callback.reset_mock()
    changed = watcher.check()  # same mtime
    assert changed is False
    callback.assert_not_called()


def test_check_detects_file_modification(tmp_path: Path) -> None:
    crontab = tmp_path / "crontab"
    crontab.write_text(SAMPLE, encoding="utf-8")
    callback = MagicMock()
    watcher = CrontabWatcher(crontab, callback)
    watcher.check()
    # Simulate modification by bumping stored mtime
    watcher._last_mtime = watcher._last_mtime - 1  # type: ignore[operator]
    changed = watcher.check()
    assert changed is True
    assert callback.call_count == 2


def test_check_missing_file_returns_true(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    callback = MagicMock()
    watcher = CrontabWatcher(missing, callback)
    changed = watcher.check()
    # mtime is None → different from initial None only after second call
    # First call: _last_mtime changes from None→None, file missing → no callback
    assert changed is True
    callback.assert_not_called()


def test_stop_prevents_further_polling(tmp_path: Path) -> None:
    crontab = tmp_path / "crontab"
    crontab.write_text(SAMPLE, encoding="utf-8")
    callback = MagicMock()
    watcher = CrontabWatcher(crontab, callback, interval=0.01)

    import threading

    thread = threading.Thread(target=watcher.start)
    thread.start()
    watcher.stop()
    thread.join(timeout=1.0)
    assert not thread.is_alive()
