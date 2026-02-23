"""
Tests for keypi_pmb.lib.pmm_client

Uses temporary directories and in-memory file content so no real
filesystem setup (OneDrive, etc.) is required.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Path setup: make keypi_pmb importable without installing Keypirinha
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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

from keypi_pmb.lib.pmm_client import (  # noqa: E402
    PmmResult,
    _parse_frontmatter,
    filter_pmm,
    format_pmm_label,
    format_pmm_short_desc,
    scan_folder,
    search_pmm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_FM = """\
---
title: Foobar implementieren
Epic: FOO-2360
Initiative: Bar-2954
tags: [foo-imp, bar-main]
---

# Content below frontmatter
"""

_NO_FM = """\
# Just a heading

No frontmatter here.
"""

_EMPTY_TAGS_FM = """\
---
title: No Tags Here
---
"""

_MINIMAL_FM = """\
---
title: Minimal Entry
---
"""


def _write_md(tmp_path, filename, content):
    """Write a markdown file to tmp_path and return its path."""
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return str(p)


def _make_result(**kwargs):
    defaults = dict(
        key="FOO-123",
        title="Foobar implementieren",
        epic="FOO-2360",
        initiative="Bar-2954",
        tags=["foo-imp", "bar-main"],
        file_path="/some/path/FOO-123.md",
        modified="2026-01-15",
    )
    defaults.update(kwargs)
    return PmmResult(**defaults)


# ---------------------------------------------------------------------------
# Tests: _parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_valid_frontmatter_parsed(self):
        fm = _parse_frontmatter(_VALID_FM)
        assert fm["title"] == "Foobar implementieren"
        assert fm["epic"] == "FOO-2360"
        assert fm["initiative"] == "Bar-2954"

    def test_tags_parsed_as_list(self):
        fm = _parse_frontmatter(_VALID_FM)
        assert fm["tags"] == ["foo-imp", "bar-main"]

    def test_missing_frontmatter_returns_empty(self):
        fm = _parse_frontmatter(_NO_FM)
        assert fm == {}

    def test_empty_tags_returns_empty_list(self):
        content = "---\ntitle: Test\ntags: []\n---\n"
        fm = _parse_frontmatter(content)
        assert fm["tags"] == []

    def test_no_tags_key_absent(self):
        fm = _parse_frontmatter(_MINIMAL_FM)
        assert "tags" not in fm

    def test_keys_are_lowercased(self):
        content = "---\nTitle: Upper\nEPIC: BIG-1\n---\n"
        fm = _parse_frontmatter(content)
        assert "title" in fm
        assert "epic" in fm

    def test_single_tag_parsed(self):
        content = "---\ntitle: X\ntags: [only-one]\n---\n"
        fm = _parse_frontmatter(content)
        assert fm["tags"] == ["only-one"]

    def test_no_trailing_content_interference(self):
        fm = _parse_frontmatter(_VALID_FM)
        assert "content below" not in fm.get("title", "")

    def test_crlf_line_endings(self):
        content = "---\r\ntitle: Windows\r\ntags: [a, b]\r\n---\r\n"
        fm = _parse_frontmatter(content)
        assert fm["title"] == "Windows"
        assert fm["tags"] == ["a", "b"]


# ---------------------------------------------------------------------------
# Tests: scan_folder
# ---------------------------------------------------------------------------


class TestScanFolder:
    def test_scans_md_files(self, tmp_path):
        _write_md(tmp_path, "FOO-123.md", _VALID_FM)
        _write_md(tmp_path, "BAR-456.md", _MINIMAL_FM)
        results = scan_folder(str(tmp_path))
        keys = [r.key for r in results]
        assert "FOO-123" in keys
        assert "BAR-456" in keys

    def test_ignores_non_md_files(self, tmp_path):
        _write_md(tmp_path, "FOO-123.md", _VALID_FM)
        (tmp_path / "notes.txt").write_text("some text")
        (tmp_path / "README.rst").write_text("rst content")
        results = scan_folder(str(tmp_path))
        assert len(results) == 1

    def test_sorted_by_key_case_insensitive(self, tmp_path):
        _write_md(tmp_path, "ZZZ-999.md", _MINIMAL_FM)
        _write_md(tmp_path, "AAA-001.md", _MINIMAL_FM)
        results = scan_folder(str(tmp_path))
        assert results[0].key == "AAA-001"
        assert results[1].key == "ZZZ-999"

    def test_nonexistent_folder_returns_empty(self):
        results = scan_folder("/this/does/not/exist/at/all")
        assert results == []

    def test_empty_string_returns_empty(self):
        results = scan_folder("")
        assert results == []

    def test_empty_folder_returns_empty(self, tmp_path):
        results = scan_folder(str(tmp_path))
        assert results == []

    def test_title_extracted_from_frontmatter(self, tmp_path):
        _write_md(tmp_path, "FOO-123.md", _VALID_FM)
        results = scan_folder(str(tmp_path))
        assert results[0].title == "Foobar implementieren"

    def test_tags_extracted_from_frontmatter(self, tmp_path):
        _write_md(tmp_path, "FOO-123.md", _VALID_FM)
        results = scan_folder(str(tmp_path))
        assert results[0].tags == ["foo-imp", "bar-main"]

    def test_epic_extracted(self, tmp_path):
        _write_md(tmp_path, "FOO-123.md", _VALID_FM)
        results = scan_folder(str(tmp_path))
        assert results[0].epic == "FOO-2360"

    def test_initiative_extracted(self, tmp_path):
        _write_md(tmp_path, "FOO-123.md", _VALID_FM)
        results = scan_folder(str(tmp_path))
        assert results[0].initiative == "Bar-2954"

    def test_key_derived_from_filename(self, tmp_path):
        _write_md(tmp_path, "PROJ-999.md", _MINIMAL_FM)
        results = scan_folder(str(tmp_path))
        assert results[0].key == "PROJ-999"

    def test_file_without_frontmatter_uses_filename_as_title(self, tmp_path):
        _write_md(tmp_path, "FOO-123.md", _NO_FM)
        results = scan_folder(str(tmp_path))
        assert results[0].title == "FOO-123"

    def test_folder_with_spaces_in_path(self, tmp_path):
        # Simulate OneDrive folder: create a subdirectory with spaces
        spaced = tmp_path / "OneDrive Folder With Spaces"
        spaced.mkdir()
        _write_md(spaced, "FOO-1.md", _MINIMAL_FM)
        results = scan_folder(str(spaced))
        assert len(results) == 1
        assert results[0].key == "FOO-1"

    def test_modified_date_format(self, tmp_path):
        _write_md(tmp_path, "FOO-123.md", _VALID_FM)
        results = scan_folder(str(tmp_path))
        modified = results[0].modified
        # Should be YYYY-MM-DD
        assert len(modified) == 10
        assert modified[4] == "-" and modified[7] == "-"


# ---------------------------------------------------------------------------
# Tests: search_pmm
# ---------------------------------------------------------------------------


class TestSearchPmm:
    def _results(self):
        return [
            _make_result(
                key="FOO-123",
                title="Steuererklaerung Feature",
                tags=["steuer", "auth"],
            ),
            _make_result(
                key="BAR-456",
                title="Deployment Pipeline",
                tags=["deploy", "ci"],
            ),
            _make_result(
                key="BAZ-789",
                title="Auth System Redesign",
                tags=["auth", "security"],
            ),
        ]

    def test_matches_title(self):
        results = search_pmm("deployment", self._results())
        assert len(results) == 1
        assert results[0].key == "BAR-456"

    def test_matches_tag(self):
        results = search_pmm("auth", self._results())
        keys = [r.key for r in results]
        assert "FOO-123" in keys
        assert "BAZ-789" in keys

    def test_matches_key(self):
        results = search_pmm("FOO-123", self._results())
        assert len(results) == 1
        assert results[0].key == "FOO-123"

    def test_case_insensitive_title(self):
        results = search_pmm("DEPLOYMENT", self._results())
        assert len(results) == 1

    def test_case_insensitive_tag(self):
        results = search_pmm("STEUER", self._results())
        assert len(results) == 1

    def test_multi_token_all_must_match(self):
        # "auth" matches FOO-123 and BAZ-789, "redesign" only BAZ-789
        results = search_pmm("auth redesign", self._results())
        assert len(results) == 1
        assert results[0].key == "BAZ-789"

    def test_no_match_returns_empty(self):
        results = search_pmm("nonexistent", self._results())
        assert results == []

    def test_empty_query_returns_empty(self):
        results = search_pmm("", self._results())
        assert results == []

    def test_whitespace_query_returns_empty(self):
        results = search_pmm("   ", self._results())
        assert results == []


# ---------------------------------------------------------------------------
# Tests: filter_pmm
# ---------------------------------------------------------------------------


class TestFilterPmm:
    def _results(self):
        return [
            _make_result(key="FOO-123", title="Steuer Feature", tags=["steuer"]),
            _make_result(key="BAR-456", title="Deploy Pipeline", tags=["deploy"]),
        ]

    def test_empty_filter_returns_all(self):
        results = filter_pmm("", self._results())
        assert len(results) == 2

    def test_filters_by_title(self):
        results = filter_pmm("steuer", self._results())
        assert len(results) == 1
        assert results[0].key == "FOO-123"

    def test_filters_by_key(self):
        results = filter_pmm("bar-456", self._results())
        assert len(results) == 1
        assert results[0].key == "BAR-456"

    def test_filters_by_tag(self):
        results = filter_pmm("deploy", self._results())
        assert len(results) == 1
        assert results[0].key == "BAR-456"

    def test_no_match_returns_empty(self):
        results = filter_pmm("nonexistent", self._results())
        assert results == []


# ---------------------------------------------------------------------------
# Tests: format helpers
# ---------------------------------------------------------------------------


class TestFormatPmmHelpers:
    def test_label_format(self):
        r = _make_result(key="FOO-123", title="Foobar implementieren")
        assert format_pmm_label(r) == "[PMM] FOO-123: Foobar implementieren"

    def test_short_desc_with_epic_and_tags(self):
        r = _make_result(epic="FOO-2360", initiative=None, tags=["foo-imp", "bar-main"])
        desc = format_pmm_short_desc(r)
        assert "Epic: FOO-2360" in desc
        assert "foo-imp" in desc
        assert "bar-main" in desc

    def test_short_desc_with_initiative(self):
        r = _make_result(initiative="Bar-2954", epic=None, tags=[])
        desc = format_pmm_short_desc(r)
        assert "Initiative: Bar-2954" in desc

    def test_short_desc_fallback_to_modified(self):
        r = _make_result(epic=None, initiative=None, tags=[], modified="2026-01-15")
        desc = format_pmm_short_desc(r)
        assert "2026-01-15" in desc

    def test_short_desc_all_fields(self):
        r = _make_result(
            epic="FOO-2360",
            initiative="Bar-2954",
            tags=["foo-imp"],
            modified="2026-01-15",
        )
        desc = format_pmm_short_desc(r)
        assert "Epic: FOO-2360" in desc
        assert "Initiative: Bar-2954" in desc
        assert "foo-imp" in desc
