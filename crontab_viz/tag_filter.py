"""Tag-based filtering for cron entries.

Allows users to annotate crontab commands with inline tags (e.g. #tag:backup)
and filter the schedule view to only show matching entries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from crontab_viz.parser import CronEntry

_TAG_RE = re.compile(r"#tag:(\w+)")


@dataclass
class TagFilterError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def extract_tags(entry: CronEntry) -> List[str]:
    """Return all tags embedded in the entry's command string.

    Tags are written as ``#tag:<name>`` anywhere in the command.
    """
    return _TAG_RE.findall(entry.command)


def filter_by_tags(
    entries: List[CronEntry],
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> List[CronEntry]:
    """Filter *entries* according to tag inclusion / exclusion rules.

    Parameters
    ----------
    entries:
        Full list of parsed cron entries.
    include:
        If provided, only entries that have **at least one** of these tags
        are kept.  An empty list raises :class:`TagFilterError`.
    exclude:
        Entries that carry **any** of these tags are removed.  Applied
        after the include filter.  An empty list raises :class:`TagFilterError`.

    Returns
    -------
    List[CronEntry]
        Filtered list preserving original order.
    """
    if include is not None and len(include) == 0:
        raise TagFilterError("include tag list must not be empty")
    if exclude is not None and len(exclude) == 0:
        raise TagFilterError("exclude tag list must not be empty")

    result = entries

    if include:
        include_set = set(include)
        result = [
            e for e in result if include_set.intersection(extract_tags(e))
        ]

    if exclude:
        exclude_set = set(exclude)
        result = [
            e for e in result if not exclude_set.intersection(extract_tags(e))
        ]

    return result


def summarise_tags(entries: List[CronEntry]) -> dict:
    """Return a mapping of tag -> count across all entries."""
    counts: dict = {}
    for entry in entries:
        for tag in extract_tags(entry):
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def entries_for_tag(entries: List[CronEntry], tag: str) -> List[CronEntry]:
    """Return all entries that contain the given *tag*.

    This is a convenience wrapper around :func:`filter_by_tags` for the
    common case of looking up a single tag without constructing an include
    list manually.

    Parameters
    ----------
    entries:
        Full list of parsed cron entries.
    tag:
        The tag name to search for (without the ``#tag:`` prefix).

    Returns
    -------
    List[CronEntry]
        Entries whose command contains ``#tag:<tag>``.
    """
    return filter_by_tags(entries, include=[tag])
