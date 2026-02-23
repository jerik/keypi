"""
PM Management File Client (PMM)

Reads local Markdown files with YAML frontmatter that serve as personal
PM management notes. Files are named <TICKET-KEY>.md (e.g. FOO-123.md).

Frontmatter format (between --- delimiters):
    ---
    title: Foobar implementieren
    Epic: FOO-2360
    Initiative: Bar-2954
    tags: [foo-imp, bar-main]
    ---

The ticket key is derived from the filename (without extension).
Tags are always in [foo, bar] notation.
Files without valid frontmatter are skipped silently.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass

# Regex to extract frontmatter block between --- delimiters
_FM_BLOCK_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---", re.DOTALL)

# Regex to extract tag list content from [foo-imp, bar-main]
_TAGS_LIST_RE = re.compile(r"\[([^\]]*)\]")


@dataclass
class PmmResult:
    """A PM management file with parsed frontmatter."""

    key: str  # Ticket key derived from filename (e.g. FOO-123)
    title: str  # From frontmatter 'title' field
    epic: str | None  # From frontmatter 'Epic' field
    initiative: str | None  # From frontmatter 'Initiative' field
    tags: list[str]  # From frontmatter 'tags' field
    file_path: str  # Absolute path to the .md file
    modified: str  # Last modified date (YYYY-MM-DD)


def scan_folder(folder: str) -> list[PmmResult]:
    """
    Scan a folder for .md files and parse their frontmatter.

    Handles folder paths with spaces (e.g. OneDrive folders).
    Files without valid frontmatter are skipped silently.

    Args:
        folder: Absolute path to the PMM folder.

    Returns:
        List of PmmResult sorted by key (case-insensitive).
    """
    if not folder or not os.path.isdir(folder):
        return []

    try:
        entries = os.listdir(folder)
    except OSError:
        return []

    results = []
    for entry in entries:
        if not entry.lower().endswith(".md"):
            continue
        file_path = os.path.join(folder, entry)
        if not os.path.isfile(file_path):
            continue

        key = os.path.splitext(entry)[0]  # FOO-123 from FOO-123.md

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        fm = _parse_frontmatter(content)

        mod_time = os.path.getmtime(file_path)
        modified = time.strftime("%Y-%m-%d", time.localtime(mod_time))

        results.append(
            PmmResult(
                key=key,
                title=fm.get("title", key),  # Fallback to filename if no title
                epic=fm.get("epic") or None,
                initiative=fm.get("initiative") or None,
                tags=fm.get("tags", []),
                file_path=file_path,
                modified=modified,
            )
        )

    results.sort(key=lambda r: r.key.lower())
    return results


def search_pmm(query: str, results: list[PmmResult]) -> list[PmmResult]:
    """
    Filter PMM results by query (all tokens must match title, key, epic, initiative, or tags).

    Case-insensitive substring match. All space-separated tokens must match.

    Args:
        query: Search terms (space-separated).
        results: All PMM results from scan_folder().

    Returns:
        Matching results in original order.
    """
    if not query.strip():
        return []

    tokens = query.lower().split()
    matched = []
    for result in results:
        searchable = (
            result.title.lower()
            + " "
            + result.key.lower()
            + " "
            + (result.epic.lower() if result.epic else "")
            + " "
            + (result.initiative.lower() if result.initiative else "")
            + " "
            + " ".join(result.tags).lower()
        )
        if all(token in searchable for token in tokens):
            matched.append(result)
    return matched


def filter_pmm(filter_text: str, results: list[PmmResult]) -> list[PmmResult]:
    """
    Filter cached PMM results by a single filter string (local filter mode).

    Matches against title, key, epic, initiative, and tags (case-insensitive substring).

    Args:
        filter_text: Single filter string (already lowercased).
        results: Previously scanned/searched PMM results.

    Returns:
        Filtered results in original order.
    """
    if not filter_text:
        return results
    return [
        r
        for r in results
        if filter_text in r.title.lower()
        or filter_text in r.key.lower()
        or (r.epic and filter_text in r.epic.lower())
        or (r.initiative and filter_text in r.initiative.lower())
        or any(filter_text in tag.lower() for tag in r.tags)
    ]


def format_pmm_label(result: PmmResult) -> str:
    """
    Format a PMM result as a Keypirinha item label.

    Example: [PMM] FOO-123: Foobar implementieren
    """
    return f"[PMM] {result.key}: {result.title}"


def format_pmm_short_desc(result: PmmResult) -> str:
    """
    Format a PMM result as a Keypirinha item short description.

    Example: Epic: FOO-2360 | Tags: foo-imp, bar-main
    """
    parts = []
    if result.epic:
        parts.append(f"Epic: {result.epic}")
    if result.initiative:
        parts.append(f"Initiative: {result.initiative}")
    if result.tags:
        parts.append(f"Tags: {', '.join(result.tags)}")
    if not parts:
        parts.append(f"Modified: {result.modified}")
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(content: str) -> dict:
    """
    Parse YAML-style frontmatter from markdown content.

    Handles simple key: value pairs and tags: [foo, bar] notation.
    Keys are lowercased for case-insensitive lookup.

    Returns:
        Dict with parsed fields. 'tags' is always a list[str].
        Empty dict if no valid frontmatter found.
    """
    m = _FM_BLOCK_RE.match(content)
    if not m:
        return {}

    result = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        result[key.strip().lower()] = val.strip()

    # Parse tags: [foo-imp, bar-main] → ['foo-imp', 'bar-main']
    if "tags" in result:
        tm = _TAGS_LIST_RE.search(result["tags"])
        if tm:
            raw = tm.group(1)
            result["tags"] = [t.strip() for t in raw.split(",") if t.strip()]
        else:
            result["tags"] = []

    return result
