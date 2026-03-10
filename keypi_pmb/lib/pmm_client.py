"""
PM Management File Client (PMM)

Reads local Markdown files with YAML frontmatter that serve as personal
PM management notes. Files may be named freely as long as the filename
contains a Jira key, e.g.:
  - FOO-123.md
  - FOO-123 - My descriptive name.md
  - 2026-02 FOO-123 Initiative foobar.md

The Jira key is extracted via regex from the filename stem.

Frontmatter format (between --- delimiters):
    ---
    title: Foobar implementieren
    initiative: INT-264
    fachkonzept: FOO-2360
    umsetzung: BAR-6852
    tags: [foo-imp, bar-main]
    Fälligkeit: 2026-02-25
    # This is a comment and will be ignored
    ---

Convention over configuration:
    - title  → display label
    - tags   → tag list (always list[str])
    - any field whose value exactly matches a Jira key pattern → drill-down ticket
    - any field whose value matches an ISO date pattern → date info (copy to clipboard)
    - lines starting with # are comments and are ignored
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field

# Regex to extract frontmatter block between --- delimiters
_FM_BLOCK_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---", re.DOTALL)

# Regex to extract tag list content from [foo-imp, bar-main]
_TAGS_LIST_RE = re.compile(r"\[([^\]]*)\]")

# Jira key anywhere in a string (for filename extraction)
_JIRA_KEY_IN_FILENAME = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")

# Exact Jira key: PROJECT-123 (alphanumeric project keys supported)
_JIRA_KEY_EXACT = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")

# ISO date: YYYY-MM-DD
_ISO_DATE_EXACT = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Confluence page ID: purely numeric (e.g. 76934384)
_CONFLUENCE_PAGE_ID_EXACT = re.compile(r"^\d+$")

# List of Jira keys: [KEY-123] or [KEY-123, BAR-456]
_JIRA_KEY_LIST_RE = re.compile(
    r"^\[([A-Z][A-Z0-9]+-\d+(?:\s*,\s*[A-Z][A-Z0-9]+-\d+)*)\]$"
)


@dataclass
class FrontmatterField:
    """A single frontmatter field (not title/tags)."""

    name: str  # Field name as written in the file (original case)
    value: str  # Field value (raw string)
    kind: str  # "jira_key" | "confluence_page_id" | "iso_date" | "text"


@dataclass
class PmmResult:
    """A PM management file with parsed frontmatter."""

    key: str  # Ticket key derived from filename (e.g. FOO-123)
    title: str  # From frontmatter 'title' field
    epic: str | None  # From frontmatter 'epic' field (legacy compat)
    initiative: str | None  # From frontmatter 'initiative' field (legacy compat)
    tags: list[str]  # From frontmatter 'tags' field
    file_path: str  # Absolute path to the .md file
    modified: str  # Last modified date (YYYY-MM-DD)
    fields: list[FrontmatterField] = field(default_factory=list)
    # All non-title, non-tags fields with kind classification.
    # Used for drill-down expansion in keypi_pmb.


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

        # Extract Jira key from filename: "FOO-123 - My Feature.md" → "FOO-123"
        stem = os.path.splitext(entry)[0]
        key_match = _JIRA_KEY_IN_FILENAME.search(stem)
        key = key_match.group(1) if key_match else stem

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        raw_lines = _parse_frontmatter_lines(content)
        fm = _parse_frontmatter(content)

        mod_time = os.path.getmtime(file_path)
        modified = time.strftime("%Y-%m-%d", time.localtime(mod_time))

        # Build typed field list (all fields except title + tags)
        # Uses raw_lines to preserve duplicate keys (e.g. two epic: entries)
        _SKIP = {"title", "tags"}
        fields = []
        for k, v in raw_lines:
            if k in _SKIP or not v:
                continue
            if _JIRA_KEY_EXACT.match(v):
                kind = "jira_key"
            elif k == "page" and _CONFLUENCE_PAGE_ID_EXACT.match(v):
                kind = "confluence_page_id"
            elif _ISO_DATE_EXACT.match(v):
                kind = "iso_date"
            elif _JIRA_KEY_LIST_RE.match(v):
                kind = "jira_key_list"
            else:
                kind = "text"
            fields.append(FrontmatterField(name=k, value=v, kind=kind))

        results.append(
            PmmResult(
                key=key,
                title=fm.get("title", key),  # Fallback to filename if no title
                epic=fm.get("epic") or None,
                initiative=fm.get("initiative") or None,
                tags=fm.get("tags", []),
                file_path=file_path,
                modified=modified,
                fields=fields,
            )
        )

    results.sort(key=lambda r: r.key.lower())
    return results


def search_pmm(query: str, results: list[PmmResult]) -> list[PmmResult]:
    """
    Filter PMM results by query (all tokens must match).

    Matches against title, key, epic, initiative, tags, and all Jira key
    field values. Case-insensitive substring match.

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
        searchable = _build_searchable(result)
        if all(token in searchable for token in tokens):
            matched.append(result)
    return matched


def filter_pmm(filter_text: str, results: list[PmmResult]) -> list[PmmResult]:
    """
    Filter cached PMM results by a single filter string (local filter mode).

    Args:
        filter_text: Single filter string (already lowercased).
        results: Previously scanned/searched PMM results.

    Returns:
        Filtered results in original order.
    """
    if not filter_text:
        return results
    return [r for r in results if filter_text in _build_searchable(r)]


def format_pmm_label(result: PmmResult) -> str:
    """
    Format a PMM result as a Keypirinha item label.

    Example: PMM: Foobar implementieren
    """
    return f"PMM: {result.title}"


def format_pmm_short_desc(result: PmmResult) -> str:
    """
    Format a PMM result as a Keypirinha item short description.

    Shows all linked Jira keys, then tags, falling back to modified date.

    Example: INT-264, FOO-2360 | Tags: foo-imp, bar-main
    """
    parts = []

    jira_keys = [f.value for f in result.fields if f.kind == "jira_key"]
    for f in result.fields:
        if f.kind == "jira_key_list":
            jira_keys.extend(parse_jira_key_list(f.value))
    if jira_keys:
        parts.append(", ".join(jira_keys))

    if result.tags:
        parts.append(f"Tags: {', '.join(result.tags)}")

    if not parts:
        parts.append(f"Modified: {result.modified}")

    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def parse_jira_key_list(value: str) -> list[str]:
    """Parse '[KEY-1, KEY-2]' into ['KEY-1', 'KEY-2']."""
    m = _TAGS_LIST_RE.search(value)
    if not m:
        return []
    return [k.strip() for k in m.group(1).split(",") if k.strip()]


def _build_searchable(result: PmmResult) -> str:
    """Build lowercase searchable string for a PmmResult."""
    parts = [
        result.title.lower(),
        result.key.lower(),
        (result.epic.lower() if result.epic else ""),
        (result.initiative.lower() if result.initiative else ""),
        " ".join(result.tags).lower(),
    ]
    # Include all field values in search; expand jira_key_list entries
    for f in result.fields:
        if f.kind == "jira_key_list":
            parts.extend(k.lower() for k in parse_jira_key_list(f.value))
        else:
            parts.append(f.value.lower())
    return " ".join(parts)


def _parse_frontmatter_lines(content: str) -> list[tuple[str, str]]:
    """
    Parse frontmatter into an ordered list of (key, value) pairs.

    Unlike _parse_frontmatter(), this preserves duplicate keys (e.g. two
    'epic:' lines both appear as separate entries). Used for drill-down
    expansion and field classification where duplicates matter.

    Keys are lowercased. Inline comments (# ...) are stripped from values.
    Lines starting with # are treated as comments and ignored.

    Returns:
        List of (key, value) tuples in order of appearance.
        Empty list if no valid frontmatter found.
    """
    m = _FM_BLOCK_RE.match(content)
    if not m:
        return []

    pairs = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = re.sub(r"\s+#.*$", "", val).strip()
        pairs.append((key.strip().lower(), val))
    return pairs


def _parse_frontmatter(content: str) -> dict:
    """
    Parse YAML-style frontmatter from markdown content.

    Handles simple key: value pairs and tags: [foo, bar] notation.
    Keys are lowercased for case-insensitive lookup.
    Lines starting with # are treated as comments and ignored.
    Inline comments (# ...) are stripped from values.
    Duplicate keys: last value wins (use _parse_frontmatter_lines for all).

    Returns:
        Dict with parsed fields. 'tags' is always a list[str].
        Empty dict if no valid frontmatter found.
    """
    pairs = _parse_frontmatter_lines(content)
    if not pairs:
        return {}

    result = dict(pairs)  # last value wins for duplicate keys

    # Parse tags: [foo-imp, bar-main] → ['foo-imp', 'bar-main']
    if "tags" in result:
        tm = _TAGS_LIST_RE.search(result["tags"])
        if tm:
            raw = tm.group(1)
            result["tags"] = [t.strip() for t in raw.split(",") if t.strip()]
        else:
            result["tags"] = []

    return result
