"""
Keypirinha Plugin: PM-Buddy (PMB)
Search Jira tickets and Confluence pages from the pm-buddy knowledge graph.
"""

from __future__ import (
    annotations,
)  # Python 3.8 compatibility: enables new-style type hints

import json
import os

import keypirinha as kp
import keypirinha_util as kpu

from .lib.pmb_client import PmbClient, PmbResult, format_label, format_short_desc


class PmBuddy(kp.Plugin):
    """
    PM-Buddy Plugin

    Two-phase workflow:
      Phase 1 (Input):  User types search term, no DB calls
      Phase 2 (Filter): Results cached, local filtering only

    Shortcuts: #edit
    Actions:   Open (default), Copy URL
    """

    VERSION = "1.0.0-dev.1"

    # Item categories
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_SHORTCUT = kp.ItemCategory.USER_BASE + 3

    # Modes
    MODE_INPUT = "input"
    MODE_FILTER = "filter"

    def __init__(self) -> None:
        super().__init__()
        self._keyword = "pmb"
        self._db_path = ""
        self._client: PmbClient | None = None
        self._current_mode = self.MODE_INPUT
        self._cached_results: list[PmbResult] = []

    # ------------------------------------------------------------------
    # Keypirinha lifecycle
    # ------------------------------------------------------------------

    def on_start(self) -> None:
        self.info(f"PmBuddy v{self.VERSION} loaded")
        self.set_actions(
            self.ITEMCAT_RESULT,
            [
                self.create_action(
                    name="open",
                    label="Open",
                    short_desc="Open in browser",
                ),
                self.create_action(
                    name="copy_url",
                    label="Copy URL",
                    short_desc="Copy URL to clipboard",
                ),
            ],
        )
        self._load_config()

    def on_catalog(self) -> None:
        self.set_catalog(
            [
                self.create_item(
                    category=self.ITEMCAT_QUERY,
                    label=self._keyword,
                    short_desc="Search pm-buddy knowledge graph",
                    target=self._keyword,
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.NOARGS,
                )
            ]
        )

    def on_suggest(self, user_input: str, items_chain: list) -> None:
        if not items_chain or items_chain[0].category() != self.ITEMCAT_QUERY:
            return

        # Re-invoked keyword while in filter mode → reset
        if len(items_chain) == 1 and self._current_mode == self.MODE_FILTER:
            self._reset_to_input_mode()

        # --- Shortcut handling ---
        if user_input.strip().startswith("#"):
            self._handle_shortcut_input(user_input.strip())
            return

        # --- Filter mode: user is narrowing cached results ---
        if self._current_mode == self.MODE_FILTER and self._cached_results:
            filter_text = user_input.strip().lower()
            filtered = self._apply_local_filter(self._cached_results, filter_text)
            self.set_suggestions(
                self._build_result_suggestions(filtered),
                kp.Match.ANY,
                kp.Sort.NONE,
            )
            return

        # --- Input mode: show hint while user types ---
        if not self._is_configured():
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Configuration missing",
                        short_desc="Please set db_path in keypi_pmb.ini",
                    )
                ]
            )
            return

        self.set_suggestions(
            [
                self.create_item(
                    category=self.ITEMCAT_QUERY,
                    label=f"{self._keyword}: {user_input}"
                    if user_input
                    else self._keyword,
                    short_desc="Press Enter to search pm-buddy",
                    target=f"search:{user_input}",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            ]
        )

    def on_execute(self, item, action) -> None:
        # --- Shortcuts ---
        if item.category() == self.ITEMCAT_SHORTCUT:
            if item.target() == "edit_config":
                self._open_config_file()
            return

        # --- Search execution (from input mode) ---
        if item.category() == self.ITEMCAT_QUERY and item.target().startswith(
            "search:"
        ):
            query = item.target()[len("search:") :]
            if query.strip():
                self._execute_search(query.strip())
            return

        # --- Result item actions ---
        if item.category() == self.ITEMCAT_RESULT:
            try:
                data = json.loads(item.data_bag())
                url = data.get("url", "")
            except Exception:
                url = item.target()

            if not action or action.name() == "open":
                if url:
                    kpu.shell_execute(url)
                self._reset_to_input_mode()
            elif action.name() == "copy_url":
                if url:
                    kpu.set_clipboard(url)
                # Don't reset — user may want to copy multiple URLs

    def on_events(self, flags: int) -> None:
        if flags & kp.Events.PACKCONFIG:
            self._load_config()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        settings = self.load_settings()
        old_keyword = self._keyword
        self._keyword = settings.get_stripped("keyword", section="main", fallback="pmb")
        self._db_path = settings.get_stripped("db_path", section="main", fallback="")

        # Expand environment variables in path (e.g. %USERPROFILE%)
        if self._db_path:
            self._db_path = os.path.expandvars(os.path.expanduser(self._db_path))

        # Re-open client if path changed
        if self._client:
            self._client.close()
            self._client = None

        if self._db_path:
            self._client = PmbClient(self._db_path)
            if not self._client.open():
                self.warn(f"Could not open pm-buddy database: {self._db_path}")
                self._client = None
            else:
                self.info(f"pm-buddy DB: {self._db_path}")
        else:
            self.warn("db_path not configured in keypi_pmb.ini")

        if old_keyword != self._keyword:
            self.on_catalog()

    def _is_configured(self) -> bool:
        return bool(self._db_path and self._client and self._client.is_open())

    def _reset_to_input_mode(self) -> None:
        self._current_mode = self.MODE_INPUT
        self._cached_results = []

    def _execute_search(self, query: str) -> None:
        """Execute search against pm-buddy DB and switch to filter mode."""
        if not self._client or not self._client.is_open():
            # Try re-opening in case DB was just created
            if self._db_path:
                self._client = PmbClient(self._db_path)
                if not self._client.open():
                    self.err(f"Cannot open pm-buddy DB: {self._db_path}")
                    return

        self.info(f"[pmb] Searching: {query!r}")
        try:
            self._cached_results = self._client.search(query, limit=50)
        except Exception as e:
            self.err(f"[pmb] Search error: {e}")
            self._cached_results = []

        self._current_mode = self.MODE_FILTER

        if not self._cached_results:
            self.set_suggestions(
                [
                    self.create_item(
                        category=kp.ItemCategory.KEYWORD,
                        label="No results found",
                        short_desc=f"No pm-buddy results for: {query}",
                        target="no_results",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                    )
                ]
            )
            return

        self.set_suggestions(
            self._build_result_suggestions(self._cached_results),
            kp.Match.ANY,
            kp.Sort.NONE,
        )

    def _apply_local_filter(
        self, results: list[PmbResult], filter_text: str
    ) -> list[PmbResult]:
        """Filter cached results by title, key, status, assignee."""
        if not filter_text:
            return results
        return [
            r
            for r in results
            if filter_text in r.title.lower()
            or filter_text in r.key.lower()
            or filter_text in (r.status or "").lower()
            or filter_text in (r.assignee or "").lower()
            or any(filter_text in tag.lower() for tag in r.tags)
        ]

    def _build_result_suggestions(self, results: list[PmbResult]) -> list:
        """Build Keypirinha suggestion items from search results."""
        suggestions = []
        for i, result in enumerate(results):
            data_bag = json.dumps(
                {
                    "url": result.url,
                    "key": result.key,
                    "title": result.title,
                    "source": result.source,
                }
            )
            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_RESULT,
                    label=format_label(result),
                    short_desc=format_short_desc(result),
                    target=f"result_{i}",  # unique target to avoid deduplication
                    data_bag=data_bag,
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )
        return suggestions

    def _handle_shortcut_input(self, user_input: str) -> None:
        """Handle shortcut input (starts with #)."""
        shortcut = user_input[1:].lower()  # strip # and lowercase
        suggestions = []

        if shortcut == "" or "edit".startswith(shortcut):
            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_SHORTCUT,
                    label="#edit",
                    short_desc="Open configuration file",
                    target="edit_config",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                )
            )

        if not suggestions:
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=f"{self._keyword}: #{shortcut}",
                    short_desc="Unknown shortcut. Available: #edit",
                    target="no_shortcut",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _open_config_file(self) -> None:
        """Open the plugin configuration file."""
        plugin_dir = os.path.dirname(__file__)
        config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_pmb.ini")
        config_path = os.path.abspath(config_path)
        self.info(f"Opening config: {config_path}")
        kpu.shell_execute(config_path)
