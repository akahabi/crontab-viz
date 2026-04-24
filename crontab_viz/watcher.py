"""File-system watcher that reloads crontab entries when the file changes."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable, List, Optional

from crontab_viz.loader import CrontabLoadError, load_file
from crontab_viz.parser import CronEntry


class CrontabWatcher:
    """Polls a crontab file for modifications and triggers a callback.

    Example usage::

        def on_change(entries):
            refresh_dashboard(entries)

        watcher = CrontabWatcher("/etc/cron.d/myjobs", on_change)
        watcher.start(interval=5)
    """

    def __init__(
        self,
        path: str | Path,
        on_change: Callable[[List[CronEntry]], None],
        interval: float = 5.0,
    ) -> None:
        self.path = Path(path)
        self.on_change = on_change
        self.interval = interval
        self._last_mtime: Optional[float] = None
        self._running = False

    def _current_mtime(self) -> Optional[float]:
        try:
            return self.path.stat().st_mtime
        except OSError:
            return None

    def check(self) -> bool:
        """Check for changes once.  Returns True if a change was detected."""
        mtime = self._current_mtime()
        if mtime != self._last_mtime:
            self._last_mtime = mtime
            if mtime is not None:
                try:
                    entries = load_file(self.path)
                    self.on_change(entries)
                except CrontabLoadError:
                    pass
            return True
        return False

    def start(self, interval: Optional[float] = None) -> None:
        """Block and poll until :meth:`stop` is called."""
        if interval is not None:
            self.interval = interval
        self._running = True
        # Trigger an immediate load on start
        self.check()
        while self._running:
            time.sleep(self.interval)
            self.check()

    def stop(self) -> None:
        """Signal the polling loop to exit."""
        self._running = False
