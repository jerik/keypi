#!/usr/bin/env python3
"""
Chrome History Preprocessor for Keypirinha
Reads Chrome's SQLite history DB and exports a clean CSV for the plugin.

Usage:
    uv run chrome_history_preprocess.py
    uv run chrome_history_preprocess.py --config C:\\path\\to\\keypi_chromehistory.ini
"""

import argparse
import configparser
import csv
import gc
import os
import shutil
import sqlite3
import tempfile


# Script location – used to auto-detect portable Keypirinha installs
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Candidate config locations, checked in order:
#   1. Portable Keypirinha: script lives in Profile/Packages/keypi_chromehistory/
#      → config is at                 Profile/User/keypi_chromehistory.ini
#   2. Standard Keypirinha install:   %APPDATA%/Keypirinha/User/...
_CONFIG_CANDIDATES = [
    os.path.normpath(
        os.path.join(_SCRIPT_DIR, "..", "..", "User", "keypi_chromehistory.ini")
    ),
    os.path.join(
        os.environ.get("APPDATA", ""),
        "Keypirinha",
        "User",
        "keypi_chromehistory.ini",
    ),
]


def find_config(explicit: str | None) -> str:
    """Return the config path to use, searching known locations if not explicit."""
    if explicit:
        return explicit
    for candidate in _CONFIG_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    # Fall back to portable path (will trigger a warning in main)
    return _CONFIG_CANDIDATES[0]


def resolve_path(path: str) -> str:
    """Expand %ENV_VAR% style variables in path."""
    return os.path.expandvars(path)


def load_config(config_path: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")
    return config


def copy_chrome_db(chrome_db_path: str) -> str:
    """Copy Chrome DB to a temp file (Chrome locks the original while running)."""
    source = resolve_path(chrome_db_path)
    if not os.path.exists(source):
        raise FileNotFoundError(f"Chrome DB not found: {source}")
    _, tmp_path = tempfile.mkstemp(suffix=".db", prefix="chrome_hist_")
    shutil.copy2(source, tmp_path)
    return tmp_path


def read_history(db_path: str) -> list:
    """Read all history entries from Chrome SQLite DB."""
    entries = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, url, last_visit_time FROM urls ORDER BY last_visit_time DESC"
        )
        for row in cursor.fetchall():
            entries.append(
                {
                    "title": row["title"] or "",
                    "url": row["url"] or "",
                    "last_visit_time": row["last_visit_time"],
                }
            )
    finally:
        conn.close()
    return entries


def apply_url_filter(entries: list, url_filter: str) -> list:
    """Keep only entries whose URL contains url_filter. Empty string keeps all."""
    if not url_filter.strip():
        return entries
    pattern = url_filter.strip().lower()
    return [e for e in entries if pattern in e["url"].lower()]


def apply_exclusion_filters(
    entries: list, exclude_titles: list, exclude_urls: list
) -> list:
    """Remove entries matching any exclusion pattern (case-insensitive substring match)."""
    title_patterns = [p.strip().lower() for p in exclude_titles if p.strip()]
    url_patterns = [p.strip().lower() for p in exclude_urls if p.strip()]
    result = []
    for entry in entries:
        title_lower = entry["title"].lower()
        url_lower = entry["url"].lower()
        if any(p in title_lower for p in title_patterns):
            continue
        if any(p in url_lower for p in url_patterns):
            continue
        result.append(entry)
    return result


def deduplicate_by_title(entries: list) -> list:
    """Keep only the most recently visited entry per title, sorted newest first."""
    seen: dict = {}
    for entry in entries:
        title = entry["title"]
        if (
            title not in seen
            or entry["last_visit_time"] > seen[title]["last_visit_time"]
        ):
            seen[title] = entry
    return sorted(seen.values(), key=lambda e: e["last_visit_time"], reverse=True)


def export_csv(entries: list, output_path: str) -> None:
    """Export entries as semicolon-separated CSV without header row."""
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        for entry in entries:
            writer.writerow([entry["title"], entry["url"]])


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess Chrome history for Keypirinha"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to keypi_chromehistory.ini (auto-detected if omitted)",
    )
    args = parser.parse_args()

    config_path = find_config(args.config)
    if os.path.exists(config_path):
        print(f"Config:  {config_path}")
    else:
        print("Warning: config not found, using built-in defaults.")
        print(f"         Searched: {', '.join(_CONFIG_CANDIDATES)}")
    config = load_config(config_path)

    chrome_db = config.get(
        "preprocess",
        "chrome_db",
        fallback=r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\History",
    )
    output_csv = resolve_path(
        config.get(
            "preprocess",
            "output_csv",
            fallback=r"%USERPROFILE%\Documents\tmp\chrome-history-clean.csv",
        )
    )
    url_filter = config.get("preprocess", "url_filter", fallback="")

    exclude_titles_raw = config.get("filter_out_titles", "exclude", fallback="")
    exclude_urls_raw = config.get("filter_out_urls", "exclude", fallback="")
    exclude_titles = [p for p in exclude_titles_raw.split(",") if p.strip()]
    exclude_urls = [p for p in exclude_urls_raw.split(",") if p.strip()]

    tmp_db = None
    try:
        print(f"Copying Chrome DB from {resolve_path(chrome_db)} ...")
        tmp_db = copy_chrome_db(chrome_db)

        print("Reading history ...")
        entries = read_history(tmp_db)
        print(f"  Total entries: {len(entries)}")

        entries = apply_url_filter(entries, url_filter)
        print(f"  After URL filter ({url_filter!r}): {len(entries)}")

        entries = apply_exclusion_filters(entries, exclude_titles, exclude_urls)
        print(f"  After exclusion filters: {len(entries)}")

        entries = deduplicate_by_title(entries)
        print(f"  After deduplication: {len(entries)}")

        export_csv(entries, output_csv)
        print(f"Exported to: {output_csv}")

    finally:
        if tmp_db:
            # On Windows, SQLite WAL mode can keep a file handle open briefly
            # after conn.close(). Force GC to release any lingering references.
            gc.collect()
            for suffix in ("", "-wal", "-shm"):
                path = tmp_db + suffix
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except PermissionError:
                        print(f"Note: temp file will be removed by OS: {path}")
            print("Cleaned up temp DB.")


if __name__ == "__main__":
    main()
