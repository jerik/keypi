"""Tests for chrome_history_preprocess.py core functions."""

import csv
import os
import sqlite3
import tempfile

from chrome_history_preprocess import (
    apply_exclusion_filters,
    apply_url_filter,
    deduplicate_by_title,
    export_csv,
    read_history,
)

SAMPLE_ENTRIES = [
    {"title": "Google", "url": "https://google.com", "last_visit_time": 100},
    {
        "title": "Jira Board",
        "url": "https://company.atlassian.net/board",
        "last_visit_time": 200,
    },
    {
        "title": "Login Page",
        "url": "https://company.atlassian.net/login",
        "last_visit_time": 150,
    },
    {
        "title": "Edit Page",
        "url": "https://company.atlassian.net/editpage",
        "last_visit_time": 120,
    },
    {
        "title": "Jira Board",
        "url": "https://company.atlassian.net/board",
        "last_visit_time": 300,
    },  # duplicate, newer
]


class TestUrlFilter:
    def test_empty_filter_keeps_all(self):
        result = apply_url_filter(SAMPLE_ENTRIES, "")
        assert len(result) == len(SAMPLE_ENTRIES)

    def test_whitespace_only_filter_keeps_all(self):
        result = apply_url_filter(SAMPLE_ENTRIES, "   ")
        assert len(result) == len(SAMPLE_ENTRIES)

    def test_filter_keeps_only_matching(self):
        result = apply_url_filter(SAMPLE_ENTRIES, "atlassian.net")
        assert all("atlassian.net" in e["url"] for e in result)
        assert len(result) == 4

    def test_filter_is_case_insensitive(self):
        result = apply_url_filter(SAMPLE_ENTRIES, "ATLASSIAN.NET")
        assert len(result) == 4

    def test_filter_no_match_returns_empty(self):
        result = apply_url_filter(SAMPLE_ENTRIES, "nonexistent.domain")
        assert result == []

    def test_filter_preserves_entry_data(self):
        result = apply_url_filter(SAMPLE_ENTRIES, "google.com")
        assert len(result) == 1
        assert result[0]["title"] == "Google"
        assert result[0]["last_visit_time"] == 100


class TestExclusionFilters:
    def test_exclude_title_pattern(self):
        result = apply_exclusion_filters(SAMPLE_ENTRIES, ["Login"], [])
        titles = [e["title"] for e in result]
        assert "Login Page" not in titles
        assert len(result) == 4

    def test_exclude_url_pattern(self):
        result = apply_exclusion_filters(SAMPLE_ENTRIES, [], ["editpage"])
        urls = [e["url"] for e in result]
        assert not any("editpage" in u for u in urls)
        assert len(result) == 4

    def test_empty_exclusions_keeps_all(self):
        result = apply_exclusion_filters(SAMPLE_ENTRIES, [], [])
        assert len(result) == len(SAMPLE_ENTRIES)

    def test_title_exclusion_case_insensitive(self):
        result = apply_exclusion_filters(SAMPLE_ENTRIES, ["LOGIN"], [])
        assert len(result) == 4

    def test_url_exclusion_case_insensitive(self):
        result = apply_exclusion_filters(SAMPLE_ENTRIES, [], ["EDITPAGE"])
        assert len(result) == 4

    def test_exclude_strips_whitespace_in_patterns(self):
        result = apply_exclusion_filters(SAMPLE_ENTRIES, ["  Login  "], [])
        titles = [e["title"] for e in result]
        assert "Login Page" not in titles

    def test_multiple_title_patterns(self):
        result = apply_exclusion_filters(SAMPLE_ENTRIES, ["Login", "Edit"], [])
        titles = [e["title"] for e in result]
        assert "Login Page" not in titles
        assert "Edit Page" not in titles
        assert len(result) == 3


class TestDeduplication:
    def test_dedup_keeps_newest_entry(self):
        result = deduplicate_by_title(SAMPLE_ENTRIES)
        jira_entries = [e for e in result if e["title"] == "Jira Board"]
        assert len(jira_entries) == 1
        assert jira_entries[0]["last_visit_time"] == 300

    def test_dedup_result_sorted_newest_first(self):
        result = deduplicate_by_title(SAMPLE_ENTRIES)
        times = [e["last_visit_time"] for e in result]
        assert times == sorted(times, reverse=True)

    def test_no_duplicates_preserves_all(self):
        unique = SAMPLE_ENTRIES[:3]
        result = deduplicate_by_title(unique)
        assert len(result) == 3

    def test_all_duplicates_keeps_one(self):
        dupes = [
            {"title": "Same", "url": "https://a.com", "last_visit_time": 50},
            {"title": "Same", "url": "https://a.com", "last_visit_time": 200},
            {"title": "Same", "url": "https://a.com", "last_visit_time": 100},
        ]
        result = deduplicate_by_title(dupes)
        assert len(result) == 1
        assert result[0]["last_visit_time"] == 200

    def test_empty_title_entries_deduplicated(self):
        entries = [
            {"title": "", "url": "https://a.com", "last_visit_time": 10},
            {"title": "", "url": "https://b.com", "last_visit_time": 20},
        ]
        result = deduplicate_by_title(entries)
        assert len(result) == 1
        assert result[0]["last_visit_time"] == 20


class TestExportCsv:
    def test_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            export_csv(SAMPLE_ENTRIES[:2], path)
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_semicolon_delimiter(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            export_csv(SAMPLE_ENTRIES[:1], path)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            assert ";" in content
        finally:
            os.unlink(path)

    def test_roundtrip_title_and_url(self):
        entries = [
            {"title": "Test Page", "url": "https://test.com", "last_visit_time": 1}
        ]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            export_csv(entries, path)
            with open(path, encoding="utf-8", newline="") as f:
                rows = list(csv.reader(f, delimiter=";"))
            assert rows[0][0] == "Test Page"
            assert rows[0][1] == "https://test.com"
        finally:
            os.unlink(path)

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "sub", "dir", "output.csv")
            export_csv(SAMPLE_ENTRIES[:1], nested_path)
            assert os.path.exists(nested_path)


class TestReadHistory:
    def _make_test_db(self) -> str:
        _, db_path = tempfile.mkstemp(suffix=".db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, title TEXT, last_visit_time INTEGER)"
        )
        conn.executemany(
            "INSERT INTO urls (url, title, last_visit_time) VALUES (?, ?, ?)",
            [
                ("https://a.com", "Page A", 300),
                ("https://b.com", "Page B", 100),
                ("https://c.com", "", 200),
            ],
        )
        conn.commit()
        conn.close()
        return db_path

    def test_reads_all_entries(self):
        db_path = self._make_test_db()
        try:
            result = read_history(db_path)
            assert len(result) == 3
        finally:
            os.unlink(db_path)

    def test_sorted_newest_first(self):
        db_path = self._make_test_db()
        try:
            result = read_history(db_path)
            times = [e["last_visit_time"] for e in result]
            assert times == sorted(times, reverse=True)
        finally:
            os.unlink(db_path)

    def test_empty_title_becomes_empty_string(self):
        db_path = self._make_test_db()
        try:
            result = read_history(db_path)
            titles = [e["title"] for e in result]
            assert "" in titles
        finally:
            os.unlink(db_path)
