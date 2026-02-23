"""
Keypirinha Plugin: PM-Buddy (PMB)
Search Jira tickets and Confluence pages from the pm-buddy knowledge graph.
Also integrates local PM management files (PMM) for personal project notes.
"""

from __future__ import (
    annotations,
)  # Python 3.8 compatibility: enables new-style type hints

import json
import os

import keypirinha as kp
import keypirinha_util as kpu

from .lib.pmb_client import PmbClient, format_label, format_short_desc
from .lib.pmm_client import (
    filter_pmm,
    format_pmm_label,
    format_pmm_short_desc,
    scan_folder,
    search_pmm,
)


class PmBuddy(kp.Plugin):
    """
    PM-Buddy Plugin

    Two-phase workflow:
      Phase 1 (Input):  User types search term, no DB/file calls
      Phase 2 (Filter): Results cached, local filtering only

    PMM results (local markdown files) always appear above DB results.

    Shortcuts: #edit, #list
    Actions:   Open (default), Copy URL (for DB results)
               Open in editor (for PMM results)
    """

    VERSION = "1.0.0-dev.3"

    # Item categories
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2  # pm-buddy DB results
    ITEMCAT_SHORTCUT = kp.ItemCategory.USER_BASE + 3
    ITEMCAT_PMM = kp.ItemCategory.USER_BASE + 4  # Local PMM file results

    # Modes
    MODE_INPUT = "input"
    MODE_FILTER = "filter"

    def __init__(self):
        super().__init__()
        self._keyword = "pmb"
        self._db_path = ""
        self._pmm_folder = ""
        self._client = None
        self._current_mode = self.MODE_INPUT
        self._cached_results = []  # DB results (list[PmbResult])
        self._cached_pmm = []  # PMM results from last search (list[PmmResult])

    # ------------------------------------------------------------------
    # Keypirinha lifecycle
    # ------------------------------------------------------------------

    def on_start(self):
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

    def on_catalog(self):
        self.set_catalog(
            [
                self.create_item(
                    category=self.ITEMCAT_QUERY,
                    label=self._keyword,
                    short_desc="Search pm-buddy knowledge graph and PM files",
                    target=self._keyword,
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.NOARGS,
                )
            ]
        )

    def on_suggest(self, user_input, items_chain):
        if not items_chain or items_chain[0].category() != self.ITEMCAT_QUERY:
            return

        # Re-invoked keyword while in filter mode → reset to input
        if len(items_chain) == 1 and self._current_mode == self.MODE_FILTER:
            self._reset_to_input_mode()

        # --- #list mode: Tab on list_pmm shortcut → show all PMM files ---
        # loop_on_suggest=True keeps this active while user types to filter
        if (
            len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target() == "list_pmm"
        ):
            # Check if pmm_folder is properly configured
            if not self._pmm_folder:
                self.set_suggestions(
                    [
                        self.create_error_item(
                            label="PMM folder not configured",
                            short_desc="Set pmm_folder in keypi_pmb.ini",
                        )
                    ]
                )
                return
            elif not os.path.isdir(self._pmm_folder):
                self.set_suggestions(
                    [
                        self.create_error_item(
                            label="PMM folder not found",
                            short_desc=f"Path does not exist: {self._pmm_folder}",
                        )
                    ]
                )
                return

            filter_text = user_input.strip().lower()
            all_pmm = scan_folder(self._pmm_folder)
            filtered = filter_pmm(filter_text, all_pmm)
            if filtered:
                self.set_suggestions(
                    self._build_pmm_suggestions(filtered), kp.Match.ANY, kp.Sort.NONE
                )
            else:
                label = "No PM files found"
                desc = (
                    f"No files match: {user_input.strip()}"
                    if user_input.strip()
                    else f"Folder is empty: {self._pmm_folder}"
                )
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label=label,
                            short_desc=desc,
                            target="no_pmm",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
            return

        # --- Tab on execute_search → run combined PMM + DB search ---
        # Pattern from JQE: Tab adds item to items_chain, on_suggest is called,
        # set_suggestions() works here (unlike in on_execute).
        if (
            self._current_mode == self.MODE_INPUT
            and len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_QUERY
            and items_chain[-1].target() == "execute_search"
        ):
            query = items_chain[-1].data_bag()
            self._execute_search(query)
            return

        # --- Shortcut handling (#edit, #list, ...) ---
        if user_input.strip().startswith("#"):
            self._handle_shortcut_input(user_input.strip())
            return

        # --- Filter mode: narrow cached results locally (no DB calls) ---
        if self._current_mode == self.MODE_FILTER and (
            self._cached_results or self._cached_pmm
        ):
            filter_text = user_input.strip().lower()
            filtered_pmm = filter_pmm(filter_text, self._cached_pmm)
            filtered_db = self._apply_local_filter(self._cached_results, filter_text)
            suggestions = self._build_pmm_suggestions(
                filtered_pmm
            ) + self._build_result_suggestions(filtered_db)
            if suggestions:
                self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
            else:
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="No results match filter",
                            short_desc=f"Filter: {user_input.strip()}",
                            target="no_filter_results",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
            return

        # --- Input mode: show hint while user types (no calls) ---
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

        # Show hint item. args_hint=REQUIRED + hit_hint=KEEPALL ensures that
        # Tab adds this item to items_chain and calls on_suggest (not on_execute).
        self.set_suggestions(
            [
                self.create_item(
                    category=self.ITEMCAT_QUERY,
                    label=f"{self._keyword}: {user_input}"
                    if user_input
                    else self._keyword,
                    short_desc="Press Tab to search pm-buddy",
                    target="execute_search",
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                    data_bag=user_input,
                )
            ]
        )

    def on_execute(self, item, action):
        # --- PMM file: open in default editor ---
        if item.category() == self.ITEMCAT_PMM:
            file_path = item.target()
            self.info(f"[pmb] Opening PMM file: {file_path}")
            kpu.shell_execute(file_path)
            self._reset_to_input_mode()
            return

        # --- Shortcuts ---
        if item.category() == self.ITEMCAT_SHORTCUT:
            if item.target() == "edit_config":
                self._open_config_file()
            return

        # --- Enter on execute_search (fallback: Launchbox closes, no results shown)
        # Tab is the correct trigger (handled in on_suggest via items_chain).
        # Enter lands here because on_execute cannot call set_suggestions() - it is ignored.
        if item.category() == self.ITEMCAT_QUERY and item.target() == "execute_search":
            self.info(
                "[pmb] Enter pressed on search item - use Tab to keep Launchbox open"
            )
            return

        # --- DB result actions ---
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

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self._load_config()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_config(self):
        settings = self.load_settings()
        old_keyword = self._keyword
        self._keyword = settings.get_stripped("keyword", section="main", fallback="pmb")
        self._db_path = settings.get_stripped("db_path", section="main", fallback="")
        self._pmm_folder = settings.get_stripped(
            "pmm_folder", section="main", fallback=""
        )

        # Expand environment variables and ~ in paths
        if self._db_path:
            self._db_path = os.path.expandvars(os.path.expanduser(self._db_path))
        if self._pmm_folder:
            self._pmm_folder = os.path.expandvars(os.path.expanduser(self._pmm_folder))

        # Re-open DB client if path changed
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

        if self._pmm_folder:
            if os.path.isdir(self._pmm_folder):
                self.info(f"PMM folder: {self._pmm_folder}")
            else:
                self.warn(f"PMM folder not found: {self._pmm_folder}")
        else:
            self.info("pmm_folder not configured - PMM features disabled")

        if old_keyword != self._keyword:
            self.on_catalog()

    def _is_configured(self):
        """At least DB or PMM folder must be configured."""
        db_ok = bool(self._db_path and self._client and self._client.is_open())
        pmm_ok = bool(self._pmm_folder and os.path.isdir(self._pmm_folder))
        return db_ok or pmm_ok

    def _reset_to_input_mode(self):
        self._current_mode = self.MODE_INPUT
        self._cached_results = []
        self._cached_pmm = []

    def _execute_search(self, query):
        """Execute search against PMM folder and pm-buddy DB, switch to filter mode."""
        # 1. PMM search (fast, local files — always first in results)
        if self._pmm_folder and os.path.isdir(self._pmm_folder):
            all_pmm = scan_folder(self._pmm_folder)
            self._cached_pmm = search_pmm(query, all_pmm)
        else:
            self._cached_pmm = []

        # 2. DB search
        if self._client and self._client.is_open():
            try:
                self._cached_results = self._client.search(query, limit=50)
            except Exception as e:
                self.err(f"[pmb] DB search error: {e}")
                self._cached_results = []
        else:
            self._cached_results = []

        self._current_mode = self.MODE_FILTER

        # Build combined suggestions: PMM always first
        suggestions = self._build_pmm_suggestions(
            self._cached_pmm
        ) + self._build_result_suggestions(self._cached_results)

        if suggestions:
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
        else:
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

    def _apply_local_filter(self, results, filter_text):
        """Filter DB results by title, key, status, assignee, or tags."""
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

    def _build_pmm_suggestions(self, results):
        """Build Keypirinha suggestion items from PMM file results."""
        suggestions = []
        for result in results:
            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_PMM,
                    label=format_pmm_label(result),
                    short_desc=format_pmm_short_desc(result),
                    target=result.file_path,  # unique per file, used for shell_execute
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )
        return suggestions

    def _build_result_suggestions(self, results):
        """Build Keypirinha suggestion items from pm-buddy DB results."""
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

    def _handle_shortcut_input(self, user_input):
        """Handle shortcut input (starts with #)."""
        shortcut = user_input[1:].lower()  # strip # and lowercase
        suggestions = []

        # #edit — open config file
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

        # #list — show all PMM files (only if pmm_folder is configured)
        if self._pmm_folder and (shortcut == "" or "list".startswith(shortcut)):
            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_SHORTCUT,
                    label="#list",
                    short_desc="Show all PM management files (type to filter)",
                    target="list_pmm",
                    args_hint=kp.ItemArgsHint.ACCEPTED,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                    loop_on_suggest=True,
                )
            )

        if not suggestions:
            available = "#edit, #list" if self._pmm_folder else "#edit"
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=f"{self._keyword}: #{shortcut}",
                    short_desc=f"Unknown shortcut. Available: {available}",
                    target="no_shortcut",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _open_config_file(self):
        """Open the plugin configuration file."""
        plugin_dir = os.path.dirname(__file__)
        config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_pmb.ini")
        config_path = os.path.abspath(config_path)
        self.info(f"Opening config: {config_path}")
        kpu.shell_execute(config_path)
