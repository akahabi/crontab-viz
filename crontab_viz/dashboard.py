"""Terminal dashboard for crontab-viz using Rich."""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from crontab_viz.formatter import format_conflicts, format_schedule_table, format_summary
from crontab_viz.loader import load_file, load_user_crontab
from crontab_viz.scheduler import detect_conflicts, schedule_all
from crontab_viz.watcher import CrontabWatcher

console = Console()


def build_layout(
    entries,
    now: Optional[datetime] = None,
    n: int = 5,
) -> Layout:
    """Build a Rich Layout from cron entries."""
    if now is None:
        now = datetime.now()

    runs = schedule_all(entries, now=now, n=n)
    conflicts = detect_conflicts(entries, now=now, window_minutes=60)

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="schedule"),
        Layout(name="conflicts"),
    )

    header_text = Text(
        f"crontab-viz  —  {now.strftime('%Y-%m-%d %H:%M:%S')}",
        justify="center",
        style="bold cyan",
    )
    layout["header"].update(Panel(header_text))
    layout["schedule"].update(
        Panel(format_schedule_table(runs), title="Upcoming Jobs")
    )
    layout["conflicts"].update(
        Panel(format_conflicts(conflicts), title="Conflicts (next 60 min)")
    )
    layout["footer"].update(
        Panel(Text(format_summary(entries, runs), justify="center"), style="dim")
    )
    return layout


def run_dashboard(
    path: Optional[str] = None,
    n: int = 5,
    refresh_seconds: float = 30.0,
    watch: bool = True,
) -> None:
    """Start the live terminal dashboard."""
    entries = load_file(path) if path else load_user_crontab()

    watcher: Optional[CrontabWatcher] = None
    if watch and path:
        watcher = CrontabWatcher(
            path,
            on_change=lambda p: None,  # reload handled in loop
        )

    try:
        with Live(console=console, refresh_per_second=1, screen=True) as live:
            import time

            last_refresh = 0.0
            while True:
                now_ts = time.monotonic()
                if watcher and watcher.check():
                    entries = load_file(path)  # type: ignore[arg-type]

                if now_ts - last_refresh >= refresh_seconds:
                    live.update(build_layout(entries, n=n))
                    last_refresh = now_ts

                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if watcher:
            watcher.stop()
