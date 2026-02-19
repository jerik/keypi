"""
PM-Buddy SQLite Client

Queries the pm-buddy SQLite database directly (no dependency on the pm-buddy
Python package). Uses the same FTS5 + tag-based search as the pm-buddy CLI,
with type-based ranking and hidden-node filtering.

Database schema (pm-buddy):
  nodes       - Jira tickets and Confluence pages
  nodes_fts   - FTS5 virtual table on (title, key)
  tags        - Auto/manual tags per node
  tags_fts    - FTS5 virtual table on tag names
  visits      - Chrome visit history per node
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Type boost scores (mirrors pm-buddy search engine)
# ---------------------------------------------------------------------------
_TYPE_BOOST: dict[str, float] = {
    "epic": 3.0,
    "initiative": 4.0,
    "story": 1.0,
    "bug": 1.0,
    "task": 1.0,
    "subtask": 0.5,
    "confluence_page": 1.5,
}
_DEFAULT_TYPE_BOOST = 1.0

# FTS5 special characters that must be quoted
_FTS5_SPECIAL = frozenset(r'-."^():/+')


@dataclass
class PmbResult:
    """A single search result from the pm-buddy database."""

    node_id: str
    node_type: str  # epic, story, bug, task, subtask, confluence_page, …
    source: str  # jira | confluence
    key: str  # PROJ-123 or Confluence page ID
    title: str
    url: str
    status: str | None
    assignee: str | None
    fix_version: str | None
    space_key: str | None
    updated: str | None
    score: float
    tags: list[str] = field(default_factory=list)


class PmbClient:
    """
    Direct SQLite client for the pm-buddy database.

    Usage:
        client = PmbClient(db_path)
        results = client.search("steuer", limit=50)
        client.close()
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open(self) -> bool:
        """
        Open the database connection.

        Returns:
            True if successful, False if db file not found / unreadable.
        """
        try:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            return True
        except Exception:
            self._conn = None
            return False

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def is_open(self) -> bool:
        """Return True if the database connection is active."""
        return self._conn is not None

    def search(self, query: str, limit: int = 50) -> list[PmbResult]:
        """
        Search the pm-buddy database for matching nodes.

        Combines FTS5 title/key search with tag-based search, applies
        type boosts and filters out hidden nodes.

        All tokens are treated as prefix searches (e.g. "steuer" matches
        "Steuererklaerung") unless the user explicitly quotes a phrase.

        Args:
            query: Search term (e.g. "steuer auth*")
            limit: Maximum number of results

        Returns:
            List of PmbResult sorted by score (highest first).
        """
        if not self._conn or not query.strip():
            return []

        safe_query = _fts5_sanitize(_add_prefix_star(query))
        candidates: dict[str, float] = {}  # node_id -> accumulated score

        # 1. FTS5 search on title + key
        try:
            rows = self._conn.execute(
                "SELECT node_id FROM nodes_fts WHERE nodes_fts MATCH ? LIMIT ?",
                (safe_query, limit * 2),
            ).fetchall()
            for i, row in enumerate(rows):
                node_id = row["node_id"]
                fts_score = max(1.0, limit - i)
                candidates[node_id] = candidates.get(node_id, 0.0) + fts_score
        except Exception:
            pass  # FTS table may not exist yet (empty DB)

        # 2. Tag-based search
        try:
            rows = self._conn.execute(
                "SELECT DISTINCT node_id FROM tags_fts WHERE tags_fts MATCH ? LIMIT ?",
                (safe_query, limit * 2),
            ).fetchall()
            for row in rows:
                node_id = row["node_id"]
                candidates[node_id] = candidates.get(node_id, 0.0) + 5.0
        except Exception:
            pass

        if not candidates:
            return []

        # 3. Fetch node details, apply boost, filter hidden
        results: list[PmbResult] = []
        for node_id, base_score in candidates.items():
            node_row = self._conn.execute(
                "SELECT id, type, source, key, title, url, status, assignee, "
                "fix_version, space_key, updated, hidden "
                "FROM nodes WHERE id = ?",
                (node_id,),
            ).fetchone()

            if not node_row or node_row["hidden"]:
                continue

            type_boost = _TYPE_BOOST.get(node_row["type"], _DEFAULT_TYPE_BOOST)

            # Recency boost from Chrome visits
            visit_row = self._conn.execute(
                "SELECT SUM(visit_count) as total FROM visits WHERE node_id = ?",
                (node_id,),
            ).fetchone()
            visit_count = (
                int(visit_row["total"]) if visit_row and visit_row["total"] else 0
            )
            recency_boost = min(visit_count * 0.5, 5.0)

            final_score = base_score * type_boost + recency_boost

            # Fetch tags
            tag_rows = self._conn.execute(
                "SELECT tag FROM tags WHERE node_id = ? ORDER BY weight DESC LIMIT 10",
                (node_id,),
            ).fetchall()
            tags = [r["tag"] for r in tag_rows]

            results.append(
                PmbResult(
                    node_id=node_id,
                    node_type=node_row["type"] or "",
                    source=node_row["source"] or "",
                    key=node_row["key"] or "",
                    title=node_row["title"] or "",
                    url=node_row["url"] or "",
                    status=node_row["status"],
                    assignee=node_row["assignee"],
                    fix_version=node_row["fix_version"],
                    space_key=node_row["space_key"],
                    updated=node_row["updated"],
                    score=final_score,
                    tags=tags,
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_prefix_star(query: str) -> str:
    """
    Append '*' to each token so FTS5 performs prefix search.

    "steuer" → "steuer*" (matches "Steuererklaerung", "Steuer", …)
    "auth*"  → "auth*"   (already has prefix star, unchanged)
    """
    tokens = query.strip().split()
    result = []
    for token in tokens:
        if not token.endswith("*"):
            token = token + "*"
        result.append(token)
    return " ".join(result)


def _fts5_sanitize(query: str) -> str:
    """
    Sanitize a user query for FTS5 MATCH.

    - Wraps tokens containing FTS5 special characters in double quotes.
    - Preserves trailing '*' as a prefix operator outside quotes.
    - Passes through plain tokens unchanged.
    """
    tokens = query.strip().split()
    sanitized: list[str] = []

    for token in tokens:
        has_prefix_star = token.endswith("*")
        base = token[:-1] if has_prefix_star else token

        if any(ch in _FTS5_SPECIAL for ch in base):
            # Escape any existing double-quotes inside the token
            escaped = base.replace('"', '""')
            result = f'"{escaped}"'
        else:
            result = base

        if has_prefix_star:
            result += "*"

        sanitized.append(result)

    return " ".join(sanitized)


def format_label(result: PmbResult) -> str:
    """
    Format a result as a Keypirinha item label.

    Jira:       KEY-123: [epic][Open] Title
    Confluence: [SPACE] Title
    """
    if result.source == "jira":
        type_str = f"[{result.node_type}]" if result.node_type else ""
        status_str = f"[{result.status}]" if result.status else ""
        return f"{result.key}: {type_str}{status_str} {result.title}"
    else:
        space_str = f"[{result.space_key}]" if result.space_key else ""
        return f"{space_str} {result.title}".strip()


def format_short_desc(result: PmbResult) -> str:
    """
    Format a result as a Keypirinha item short description.

    Jira:       Assignee: Max | Fix: 1.2.0
    Confluence: Type: page | Modified: 2026-01-15
    """
    if result.source == "jira":
        parts = []
        if result.assignee:
            parts.append(f"Assignee: {result.assignee}")
        if result.fix_version:
            parts.append(f"Fix: {result.fix_version}")
        if result.tags:
            parts.append(f"Tags: {', '.join(result.tags[:5])}")
        return " | ".join(parts) if parts else result.url
    else:
        parts = []
        if result.node_type:
            parts.append(f"Type: {result.node_type}")
        if result.updated:
            date_str = result.updated[:10] if result.updated else ""
            if date_str:
                parts.append(f"Modified: {date_str}")
        if result.tags:
            parts.append(f"Tags: {', '.join(result.tags[:5])}")
        return " | ".join(parts) if parts else result.url
