"""
Tests for keypi_pmb.lib.pmb_client

Uses an in-memory SQLite database with the same schema as pm-buddy,
so no pm-buddy installation is required to run tests.
"""

import sqlite3
import sys
import os

import pytest

# ---------------------------------------------------------------------------
# Path setup: make keypi_pmb importable without installing Keypirinha
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Stub out keypirinha modules so we can import keypi_pmb without Keypirinha
import types

kp_stub = types.ModuleType("keypirinha")
kp_stub.Plugin = object
kp_stub.ItemCategory = types.SimpleNamespace(USER_BASE=0, KEYWORD=99)
kp_stub.ItemArgsHint = types.SimpleNamespace(REQUIRED=0, FORBIDDEN=1, ACCEPTED=2)
kp_stub.ItemHitHint = types.SimpleNamespace(NOARGS=0, IGNORE=1, KEEPALL=2)
kp_stub.Match = types.SimpleNamespace(ANY=0)
kp_stub.Sort = types.SimpleNamespace(NONE=0)
kp_stub.Events = types.SimpleNamespace(PACKCONFIG=1)
sys.modules.setdefault("keypirinha", kp_stub)
sys.modules.setdefault("keypirinha_util", types.ModuleType("keypirinha_util"))

from keypi_pmb.lib.pmb_client import (  # noqa: E402
    NodeDetail,
    PmbClient,
    PmbResult,
    _fts5_sanitize,
    format_label,
    format_short_desc,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _create_schema(conn: sqlite3.Connection) -> None:
    """Create pm-buddy schema in the given connection (including settings table)."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            type TEXT,
            source TEXT,
            key TEXT,
            title TEXT,
            url TEXT,
            status TEXT,
            priority TEXT,
            assignee TEXT,
            fix_version TEXT,
            due_date TEXT,
            labels TEXT DEFAULT '[]',
            components TEXT DEFAULT '[]',
            created TEXT,
            updated TEXT,
            space_key TEXT,
            body_storage TEXT,
            raw_json TEXT,
            synced_at TEXT,
            hidden INTEGER DEFAULT 0
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
            node_id UNINDEXED,
            title,
            key
        );

        CREATE TABLE IF NOT EXISTS tags (
            node_id TEXT,
            tag TEXT,
            source TEXT,
            weight REAL DEFAULT 1.0,
            PRIMARY KEY (node_id, tag)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS tags_fts USING fts5(
            node_id UNINDEXED,
            tag
        );

        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            url TEXT,
            visit_time TEXT,
            visit_count INTEGER DEFAULT 1
        );
        """
    )


def _insert_node(
    conn,
    id,
    type_,
    source,
    key,
    title,
    url,
    status=None,
    assignee=None,
    fix_version=None,
    space_key=None,
    updated=None,
    hidden=0,
) -> None:
    conn.execute(
        "INSERT INTO nodes (id, type, source, key, title, url, status, assignee, "
        "fix_version, space_key, updated, hidden) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            id,
            type_,
            source,
            key,
            title,
            url,
            status,
            assignee,
            fix_version,
            space_key,
            updated,
            hidden,
        ),
    )
    conn.execute(
        "INSERT INTO nodes_fts (node_id, title, key) VALUES (?, ?, ?)",
        (id, title, key),
    )


def _insert_tag(conn, node_id, tag, weight=1.0) -> None:
    conn.execute(
        "INSERT INTO tags (node_id, tag, source, weight) VALUES (?, ?, 'auto', ?)",
        (node_id, tag, weight),
    )
    conn.execute(
        "INSERT INTO tags_fts (node_id, tag) VALUES (?, ?)",
        (node_id, tag),
    )


def _make_client_with_conn(conn: sqlite3.Connection) -> PmbClient:
    """Create a PmbClient that uses an existing in-memory connection."""
    client = PmbClient(":memory:")
    client._conn = conn
    conn.row_factory = sqlite3.Row
    return client


@pytest.fixture()
def db_conn():
    """Provides a fresh in-memory SQLite connection with pm-buddy schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _create_schema(conn)
    yield conn
    conn.close()


@pytest.fixture()
def client(db_conn):
    """Provides a PmbClient wired to the in-memory DB fixture."""
    return _make_client_with_conn(db_conn)


# ---------------------------------------------------------------------------
# Tests: _fts5_sanitize
# ---------------------------------------------------------------------------


class TestFts5Sanitize:
    def test_plain_token(self):
        assert _fts5_sanitize("auth") == "auth"

    def test_prefix_star_preserved(self):
        assert _fts5_sanitize("auth*") == "auth*"

    def test_hyphen_quoted(self):
        assert _fts5_sanitize("pm-buddy") == '"pm-buddy"'

    def test_dot_quoted(self):
        assert _fts5_sanitize("1.2.0") == '"1.2.0"'

    def test_hyphen_with_prefix_star(self):
        # base has hyphen → quoted, but star must survive outside quotes
        result = _fts5_sanitize("pm-buddy*")
        assert result == '"pm-buddy"*'

    def test_multiple_tokens(self):
        result = _fts5_sanitize("auth steuer")
        assert result == "auth steuer"

    def test_mixed_tokens(self):
        result = _fts5_sanitize("auth* pm-buddy")
        assert result == 'auth* "pm-buddy"'

    def test_empty_query(self):
        assert _fts5_sanitize("") == ""


# ---------------------------------------------------------------------------
# Tests: PmbClient.search
# ---------------------------------------------------------------------------


class TestPmbClientSearch:
    def test_search_returns_matching_node(self, client, db_conn):
        _insert_node(
            db_conn,
            "jira:PROJ-1",
            "story",
            "jira",
            "PROJ-1",
            "Steuererklaerung Feature",
            "https://jira/PROJ-1",
            status="Open",
        )
        db_conn.commit()

        results = client.search("steuer")
        assert len(results) == 1
        assert results[0].key == "PROJ-1"
        assert results[0].title == "Steuererklaerung Feature"

    def test_hidden_node_excluded(self, client, db_conn):
        _insert_node(
            db_conn,
            "jira:PROJ-2",
            "story",
            "jira",
            "PROJ-2",
            "Hidden Ticket",
            "https://jira/PROJ-2",
            hidden=1,
        )
        db_conn.commit()

        results = client.search("hidden")
        assert results == []

    def test_empty_query_returns_empty(self, client):
        results = client.search("")
        assert results == []

    def test_whitespace_query_returns_empty(self, client):
        results = client.search("   ")
        assert results == []

    def test_tag_search_finds_node(self, client, db_conn):
        _insert_node(
            db_conn,
            "jira:PROJ-3",
            "epic",
            "jira",
            "PROJ-3",
            "Auth System",
            "https://jira/PROJ-3",
        )
        _insert_tag(db_conn, "jira:PROJ-3", "authentication")
        db_conn.commit()

        results = client.search("authentication")
        assert any(r.key == "PROJ-3" for r in results)

    def test_epic_ranks_higher_than_story(self, client, db_conn):
        _insert_node(
            db_conn,
            "jira:STORY-1",
            "story",
            "jira",
            "STORY-1",
            "Deployment Process",
            "https://jira/STORY-1",
        )
        _insert_node(
            db_conn,
            "jira:EPIC-1",
            "epic",
            "jira",
            "EPIC-1",
            "Deployment Epic",
            "https://jira/EPIC-1",
        )
        db_conn.commit()

        results = client.search("deployment")
        assert len(results) == 2
        assert results[0].node_type == "epic"  # epic should rank first

    def test_confluence_page_returned(self, client, db_conn):
        _insert_node(
            db_conn,
            "confluence:99999",
            "confluence_page",
            "confluence",
            "99999",
            "Fachkonzept Steuern",
            "https://confluence/wiki/Fachkonzept",
            space_key="STEU",
            updated="2026-01-15T10:00:00",
        )
        db_conn.commit()

        results = client.search("fachkonzept")
        assert len(results) == 1
        assert results[0].source == "confluence"
        assert results[0].space_key == "STEU"

    def test_visit_boost_applied(self, client, db_conn):
        _insert_node(
            db_conn,
            "jira:PROJ-4",
            "story",
            "jira",
            "PROJ-4",
            "Frequently Visited",
            "https://jira/PROJ-4",
        )
        _insert_node(
            db_conn,
            "jira:PROJ-5",
            "story",
            "jira",
            "PROJ-5",
            "Rarely Visited",
            "https://jira/PROJ-5",
        )
        db_conn.execute(
            "INSERT INTO visits (node_id, url, visit_time, visit_count) VALUES (?,?,?,?)",
            ("jira:PROJ-4", "https://jira/PROJ-4", "2026-01-01", 10),
        )
        db_conn.commit()

        results = client.search("visited")
        freq = next(r for r in results if r.key == "PROJ-4")
        rare = next(r for r in results if r.key == "PROJ-5")
        assert freq.score > rare.score

    def test_no_connection_returns_empty(self):
        client = PmbClient(":memory:")
        # Do NOT call open() — connection is None
        results = client.search("anything")
        assert results == []

    def test_limit_respected(self, client, db_conn):
        for i in range(20):
            _insert_node(
                db_conn,
                f"jira:PROJ-{i + 100}",
                "story",
                "jira",
                f"PROJ-{i + 100}",
                f"Ticket number {i}",
                f"https://jira/PROJ-{i + 100}",
            )
        db_conn.commit()

        results = client.search("ticket", limit=5)
        assert len(results) <= 5


# ---------------------------------------------------------------------------
# Tests: format_label and format_short_desc
# ---------------------------------------------------------------------------


class TestFormatHelpers:
    def _make_jira_result(self, **kwargs) -> PmbResult:
        defaults = dict(
            node_id="jira:PROJ-1",
            node_type="epic",
            source="jira",
            key="PROJ-1",
            title="Steuererklaerung",
            url="https://jira/PROJ-1",
            status="Open",
            assignee="Max Mustermann",
            fix_version="1.2.0",
            space_key=None,
            updated=None,
            score=10.0,
            tags=["steuer", "auth"],
        )
        defaults.update(kwargs)
        return PmbResult(**defaults)

    def _make_confluence_result(self, **kwargs) -> PmbResult:
        defaults = dict(
            node_id="confluence:99999",
            node_type="confluence_page",
            source="confluence",
            key="99999",
            title="Fachkonzept Steuern",
            url="https://conf/wiki/steuern",
            status=None,
            assignee=None,
            fix_version=None,
            space_key="STEU",
            updated="2026-01-15T10:00:00",
            score=5.0,
            tags=["steuern", "konzept"],
        )
        defaults.update(kwargs)
        return PmbResult(**defaults)

    def test_jira_label_contains_key_type_status_title(self):
        r = self._make_jira_result()
        label = format_label(r)
        assert "PROJ-1" in label
        assert "epic" in label
        assert "Open" in label
        assert "Steuererklaerung" in label

    def test_confluence_label_contains_space_and_title(self):
        r = self._make_confluence_result()
        label = format_label(r)
        assert "STEU" in label
        assert "Fachkonzept Steuern" in label

    def test_jira_short_desc_contains_assignee_and_fix(self):
        r = self._make_jira_result()
        desc = format_short_desc(r)
        assert "Max Mustermann" in desc
        assert "1.2.0" in desc

    def test_confluence_short_desc_contains_type_and_date(self):
        r = self._make_confluence_result()
        desc = format_short_desc(r)
        assert "confluence_page" in desc
        assert "2026-01-15" in desc

    def test_jira_no_assignee_falls_back_to_url(self):
        r = self._make_jira_result(assignee=None, fix_version=None, tags=[])
        desc = format_short_desc(r)
        assert "https://jira/PROJ-1" in desc

    def test_confluence_no_updated_shows_type_only(self):
        r = self._make_confluence_result(updated=None, tags=[])
        desc = format_short_desc(r)
        assert "confluence_page" in desc


# ---------------------------------------------------------------------------
# Tests: get_node_by_key
# ---------------------------------------------------------------------------


class TestGetNodeByKey:
    def test_returns_node_detail_for_existing_key(self, db_conn):
        _insert_node(
            db_conn,
            id="jira:FOO-1",
            type_="epic",
            source="jira",
            key="FOO-1",
            title="Foobar Epic",
            url="https://acme.atlassian.net/browse/FOO-1",
            status="In Progress",
            fix_version="2026.03",
        )
        db_conn.commit()
        client = _make_client_with_conn(db_conn)
        detail = client.get_node_by_key("FOO-1")
        assert detail is not None
        assert isinstance(detail, NodeDetail)
        assert detail.key == "FOO-1"
        assert detail.node_type == "epic"
        assert detail.title == "Foobar Epic"
        assert detail.status == "In Progress"
        assert detail.fix_version == "2026.03"
        assert "FOO-1" in detail.url

    def test_returns_none_for_missing_key(self, db_conn):
        client = _make_client_with_conn(db_conn)
        assert client.get_node_by_key("MISSING-999") is None

    def test_only_returns_jira_source(self, db_conn):
        """Confluence pages are not returned even if they have a key match."""
        _insert_node(
            db_conn,
            id="confluence:FOO-1",
            type_="confluence_page",
            source="confluence",
            key="FOO-1",
            title="Some Confluence Page",
            url="https://acme.atlassian.net/wiki/FOO-1",
        )
        db_conn.commit()
        client = _make_client_with_conn(db_conn)
        assert client.get_node_by_key("FOO-1") is None

    def test_optional_fields_none_when_missing(self, db_conn):
        _insert_node(
            db_conn,
            id="jira:BAR-2",
            type_="story",
            source="jira",
            key="BAR-2",
            title="Simple Story",
            url="https://acme.atlassian.net/browse/BAR-2",
        )
        db_conn.commit()
        client = _make_client_with_conn(db_conn)
        detail = client.get_node_by_key("BAR-2")
        assert detail is not None
        assert detail.status is None
        assert detail.fix_version is None

    def test_returns_none_when_db_closed(self):
        client = PmbClient(":memory:")
        assert client.get_node_by_key("FOO-1") is None


# ---------------------------------------------------------------------------
# Tests: get_setting
# ---------------------------------------------------------------------------


class TestGetSetting:
    def test_returns_value_for_existing_key(self, db_conn):
        db_conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("atlassian_url", "https://acme.atlassian.net"),
        )
        db_conn.commit()
        client = _make_client_with_conn(db_conn)
        assert client.get_setting("atlassian_url") == "https://acme.atlassian.net"

    def test_returns_none_for_missing_key(self, db_conn):
        client = _make_client_with_conn(db_conn)
        assert client.get_setting("nonexistent") is None

    def test_returns_none_when_db_closed(self):
        client = PmbClient(":memory:")
        assert client.get_setting("atlassian_url") is None

    def test_returns_none_when_settings_table_missing(self):
        """Handles DBs without settings table (migration not applied)."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        # Create schema WITHOUT settings table
        conn.execute(
            "CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT, source TEXT, "
            "key TEXT, title TEXT, url TEXT, status TEXT, assignee TEXT, "
            "fix_version TEXT, space_key TEXT, updated TEXT, hidden INTEGER DEFAULT 0)"
        )
        conn.commit()
        client = _make_client_with_conn(conn)
        assert client.get_setting("atlassian_url") is None
        conn.close()
