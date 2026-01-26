"""
Keypirinha Plugin: Confluence Query Explorer (CQE)
Query Confluence Cloud using CQL directly from Keypirinha launcher
"""

import keypirinha as kp
import keypirinha_util as kpu
import os
import sys
import json
import re

# Add lib directory to path
_LIB_DIR = os.path.join(os.path.dirname(__file__), "lib")
sys.path.insert(0, _LIB_DIR)

from confluence_client import (  # noqa: E402
    ConfluenceClient,
    ConfluenceAuthError,
    ConfluenceAPIError,
    ConfluenceNetworkError,
)


class ConfluenceQueryExplorer(kp.Plugin):
    """
    Confluence Query Explorer Plugin
    Allows querying Confluence Cloud using CQL from Keypirinha
    """

    # Version
    VERSION = "1.2.0-dev.1"

    # Constants
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_FILTER = kp.ItemCategory.USER_BASE + 3
    ITEMCAT_SHORTCUT = kp.ItemCategory.USER_BASE + 4

    # Modes
    MODE_CQL = "cql"
    MODE_FILTER = "filter"

    # Action names (for set_actions)
    ACTION_OPEN = "open"
    ACTION_COPY_URL = "copy_url"
    ACTION_EDIT = "edit"

    def __init__(self):
        super().__init__()
        # Confluence connection
        self.confluence_client = None
        self.confluence_url = None
        self.email = None
        self.api_token = None

        # State management for filter feature
        self._keyword = "cqe"  # Default keyword, configurable
        self._current_mode = self.MODE_CQL
        self._current_cql = ""
        self._cached_results = []
        self._filter_text = ""

        # CQL Shortcuts
        self._cql_shortcuts = {}  # {shortcut_name: cql_query}

    def on_start(self):
        """Called when plugin is loaded"""
        self.info(f"ConfluenceQueryExplorer v{self.VERSION} loaded")
        # Reset state to ensure clean start
        self._reset_to_cql_mode()

        # Register actions for result items
        self.set_actions(
            self.ITEMCAT_RESULT,
            [
                self.create_action(
                    name=self.ACTION_OPEN,
                    label="Open page",
                    short_desc="Open page in browser (default)",
                ),
                self.create_action(
                    name=self.ACTION_COPY_URL,
                    label="Copy URL",
                    short_desc="Copy page URL to clipboard",
                ),
                self.create_action(
                    name=self.ACTION_EDIT,
                    label="Edit page",
                    short_desc="Open page in edit mode",
                ),
            ],
        )

    def on_catalog(self):
        """
        Populate the catalog with plugin items
        Called when Keypirinha updates its catalog
        """
        catalog = [
            self.create_item(
                category=self.ITEMCAT_QUERY,
                label=self._keyword,
                short_desc="Query Confluence using CQL",
                target=self._keyword,
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.NOARGS,
            )
        ]
        self.set_catalog(catalog)

    def on_suggest(self, user_input, items_chain):
        """
        Handle user input and provide suggestions

        Args:
            user_input: Current user input string
            items_chain: Chain of selected items
        """
        self.dbg(
            f"[on_suggest] user_input='{user_input}', mode={self._current_mode}, cached={len(self._cached_results)}"
        )

        # Only process if our keyword is in the chain
        if not items_chain or items_chain[0].category() != self.ITEMCAT_QUERY:
            return

        # Load configuration if not already loaded
        if not self.confluence_client:
            self._load_config()

        # Check if configuration is valid
        if not self._is_configured():
            self.warn("Configuration missing - check keypi_cqe.ini")
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Configuration missing",
                        short_desc="Please configure your Confluence credentials in keypi_cqe.ini",
                    )
                ]
            )
            return

        # IMPORTANT: Reset to CQL mode if user re-invokes keyword
        # This allows starting a new query even if stuck in FILTER mode
        if len(items_chain) == 1 and self._current_mode == self.MODE_FILTER:
            self.info("User re-invoked keyword - resetting to CQL mode for new query")
            self._reset_to_cql_mode()

        # Check if user pressed Tab on the "execute_cql" item
        # This happens when items_chain has 2 items: [keyword, execute_cql]
        # IMPORTANT: Only execute in CQL mode, not in FILTER mode!
        if (
            self._current_mode == self.MODE_CQL
            and len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_QUERY
            and items_chain[-1].target() == "execute_cql"
        ):
            cql_query = items_chain[-1].data_bag()
            self.dbg(f"Tab pressed on execute_cql in CQL mode: '{cql_query}'")
            self._execute_cql_query(cql_query)
            # After query execution, on_suggest will be called again
            # and we'll be in FILTER mode with cached results
            return

        # Check if user selected a shortcut (pressed Enter/Tab)
        # Show the expanded CQL as an "execute_cql" item (like manual CQL input)
        if (
            self._current_mode == self.MODE_CQL
            and len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target().startswith("shortcut_")
        ):
            cql_query = items_chain[-1].data_bag()
            shortcut_name = items_chain[-1].target().replace("shortcut_", "")
            self.info(
                f"Shortcut #{shortcut_name} selected, showing CQL: {cql_query[:50]}..."
            )

            # Show CQL as execute item (same as manual CQL input)
            # KEEPALL keeps Keypirinha open for Tab execution
            self.set_suggestions(
                [
                    self.create_item(
                        category=self.ITEMCAT_QUERY,
                        label=f"{self._keyword}: {cql_query}",
                        short_desc="Press Tab to execute query, or Esc to go back",
                        target="execute_cql",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                        data_bag=cql_query,
                    )
                ],
                kp.Match.ANY,
                kp.Sort.NONE,
            )
            return

        # Check if user pressed Tab/Enter on #edit
        # Open config file and reset to allow new query
        if (
            len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target() == "edit_config"
        ):
            plugin_dir = os.path.dirname(__file__)
            config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_cqe.ini")
            config_path = os.path.abspath(config_path)
            self.info(f"Opening config file: {config_path}")
            kpu.shell_execute(config_path)
            self._reset_to_cql_mode()
            return

        self.dbg(f"MODE={self._current_mode}, CQL='{self._current_cql}'")

        # State machine: Handle CQL mode vs Filter mode
        if self._current_mode == self.MODE_CQL:
            # CQL Input Mode - NO API calls during typing
            if not user_input.strip():
                # Show hint if no input
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="Enter CQL query or #shortcut...",
                            short_desc="Example: type=page AND space=MYSPACE | Use # for shortcuts",
                            target="hint",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
            elif user_input.strip().startswith("#"):
                # Shortcut mode - show available shortcuts
                self._handle_shortcut_input(user_input.strip())
            else:
                # User is typing CQL - show "Press Enter" hint (NO API call)
                self.dbg(f"CQL_MODE: typing '{user_input.strip()[:30]}...'")
                self.set_suggestions(
                    [
                        self.create_item(
                            category=self.ITEMCAT_QUERY,
                            label=f"{self._keyword}: {user_input.strip()}",
                            short_desc="Press Enter to execute query",
                            target="execute_cql",
                            args_hint=kp.ItemArgsHint.REQUIRED,
                            hit_hint=kp.ItemHitHint.KEEPALL,
                            data_bag=user_input.strip(),
                        )
                    ]
                )

        elif self._current_mode == self.MODE_FILTER:
            # Filter Mode - filter cached results locally
            filter_text = user_input.strip()
            self._filter_text = filter_text

            if not filter_text:
                # No filter - show all cached results
                self.dbg(f"FILTER: showing all {len(self._cached_results)} results")
                filtered_results = self._cached_results
            else:
                # Filter cached results
                filtered_results = self._filter_results(filter_text)
                self.dbg(f"FILTER: '{filter_text}' -> {len(filtered_results)} results")

            if not filtered_results:
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label=f"{self._keyword}: filter mode",
                            short_desc=f"No results match filter: {filter_text}",
                            target="no_results",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
            else:
                # Display filtered results
                suggestions = []
                for item in filtered_results:
                    label = f"{item['title']}"
                    # Format: Space: FOO | Type: page | LastMod: 2026-01-21
                    last_mod = item.get("last_modified", "N/A")
                    short_desc = f"Space: {item['space_name']} | Type: {item['type']} | LastMod: {last_mod}"

                    suggestions.append(
                        self.create_item(
                            category=self.ITEMCAT_RESULT,
                            label=label,
                            short_desc=short_desc,
                            target=item["url"],
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                            data_bag=json.dumps(item),
                        )
                    )
                self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _execute_cql_query(self, cql_query):
        """
        Execute CQL query and cache results

        Args:
            cql_query: CQL query string
        """
        self.info(f"Executing CQL: {cql_query[:50]}...")
        try:
            # Query Confluence API
            content_items = self.confluence_client.search_content(
                cql_query, max_results=50
            )

            # Cache the CQL and results
            self._current_cql = cql_query
            self._cached_results = content_items if content_items else []

            # Switch to FILTER mode
            self._current_mode = self.MODE_FILTER
            self._filter_text = ""

            if not content_items:
                self.info("Query returned 0 results")
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label=f"{self._keyword}: filter mode",
                            short_desc=f"No content found for query: {cql_query[:50]}...",
                            target="no_results",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
                return

            # Create suggestion items from results
            suggestions = []
            for item in content_items:
                # Format: Title
                label = f"{item['title']}"

                # Additional info for description
                # Format: Space: FOO | Type: page | LastMod: 2026-01-21
                last_mod = item.get("last_modified", "N/A")
                short_desc = f"Space: {item['space_name']} | Type: {item['type']} | LastMod: {last_mod}"

                suggestions.append(
                    self.create_item(
                        category=self.ITEMCAT_RESULT,
                        label=label,
                        short_desc=short_desc,
                        target=item["url"],
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                        data_bag=json.dumps(item),
                    )
                )

            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
            self.info(f"Query successful: {len(content_items)} results cached")

        except ConfluenceAuthError as e:
            self.err(f"[_execute_cql_query] ConfluenceAuthError: {str(e)}")
            self._current_mode = self.MODE_CQL
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Authentication failed", short_desc=str(e)
                    )
                ]
            )

        except ConfluenceAPIError as e:
            self.err(f"[_execute_cql_query] ConfluenceAPIError: {str(e)}")
            self._current_mode = self.MODE_CQL
            self.set_suggestions(
                [self.create_error_item(label="API error", short_desc=str(e))]
            )

        except ConfluenceNetworkError as e:
            self.err(f"[_execute_cql_query] ConfluenceNetworkError: {str(e)}")
            self._current_mode = self.MODE_CQL
            self.set_suggestions(
                [self.create_error_item(label="Network error", short_desc=str(e))]
            )

        except Exception as e:
            self.err(f"[_execute_cql_query] Unexpected error: {str(e)}")
            import traceback

            self.err(f"[_execute_cql_query] Traceback: {traceback.format_exc()}")
            self._current_mode = self.MODE_CQL
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Unexpected error",
                        short_desc=f"An error occurred: {str(e)}",
                    )
                ]
            )

    def on_execute(self, item, action):
        """
        Execute action on selected item

        Args:
            item: Selected catalog item
            action: Action to execute (can be None for default action)
        """
        # Handle CQL mode - Execute query when Enter is pressed (fallback)
        # NOTE: Tab is recommended (keeps Launchbox open), Enter closes it
        if item.category() == self.ITEMCAT_QUERY and item.target() == "execute_cql":
            cql_query = item.data_bag()
            self.info(f"Enter pressed - executing: {cql_query[:50]}...")
            self._execute_cql_query(cql_query)

        # Handle shortcut selection - Show CQL for review (not execute directly)
        # This allows user to see the query before executing with Tab
        elif item.category() == self.ITEMCAT_SHORTCUT and item.target().startswith(
            "shortcut_"
        ):
            cql_query = item.data_bag()
            shortcut_name = item.target().replace("shortcut_", "")
            self.info(
                f"Shortcut #{shortcut_name} selected via Enter, showing CQL: {cql_query[:50]}..."
            )

            # Show CQL as execute item (same as manual CQL input)
            # KEEPALL keeps Keypirinha open for Tab execution
            self.set_suggestions(
                [
                    self.create_item(
                        category=self.ITEMCAT_QUERY,
                        label=f"{self._keyword}: {cql_query}",
                        short_desc="Press Tab to execute query, or Esc to go back",
                        target="execute_cql",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                        data_bag=cql_query,
                    )
                ],
                kp.Match.ANY,
                kp.Sort.NONE,
            )

        # Handle #edit - Open config file
        elif (
            item.category() == self.ITEMCAT_SHORTCUT and item.target() == "edit_config"
        ):
            # Get config file path - use relative path from plugin directory
            # Plugin is in: Packages/keypi_cqe/
            # Config is in:  User/keypi_cqe.ini
            plugin_dir = os.path.dirname(__file__)
            config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_cqe.ini")
            config_path = os.path.abspath(config_path)
            self.info(f"Opening config file: {config_path}")
            # Open config file with default editor
            kpu.shell_execute(config_path)

        # Handle RESULT items with actions
        elif item.category() == self.ITEMCAT_RESULT:
            item_data = json.loads(item.data_bag())
            page_url = item.target()
            page_id = item_data["id"]

            if not action:
                # Default action (Enter): Open page
                self.info(f"Default action: Opening content {page_id}")
                kpu.shell_execute(page_url)
                self._reset_to_cql_mode()

            elif action.name() == self.ACTION_OPEN:
                # Open page action
                self.info(f"Action: Open page - {page_url}")
                kpu.shell_execute(page_url)
                self._reset_to_cql_mode()

            elif action.name() == self.ACTION_COPY_URL:
                # Copy URL to clipboard
                self.info(f"Action: Copy URL - {page_url}")
                kpu.set_clipboard(page_url)
                # Don't reset mode - user might want to copy multiple URLs

            elif action.name() == self.ACTION_EDIT:
                # Open page in edit mode
                edit_url = self._generate_edit_url(page_url, page_id)
                self.info(f"Action: Edit page - {edit_url}")
                kpu.shell_execute(edit_url)
                self._reset_to_cql_mode()

    def _reset_to_cql_mode(self):
        """Reset plugin state to CQL mode"""
        self.dbg(f"Resetting to CQL mode, clearing {len(self._cached_results)} results")
        self._current_mode = self.MODE_CQL
        self._current_cql = ""
        self._cached_results = []
        self._filter_text = ""

    def on_events(self, flags):
        """
        Handle events (e.g., configuration changes)

        Args:
            flags: Event flags
        """
        if flags & kp.Events.PACKCONFIG:
            # Configuration changed, reload
            self._load_config()

    def _load_config(self):
        """Load configuration from INI file"""
        settings = self.load_settings()

        # Read main configuration
        self.confluence_url = settings.get_stripped(
            "confluence_url", section="main", fallback=""
        )

        self.email = settings.get_stripped(
            "atlassian_email", section="main", fallback=""
        )

        self.api_token = settings.get_stripped(
            "atlassian_api_key", section="main", fallback=""
        )

        # Read keyword configuration (default: "cqe")
        old_keyword = self._keyword
        self._keyword = settings.get_stripped("keyword", section="main", fallback="cqe")

        # If keyword changed, update catalog
        if old_keyword != self._keyword:
            self.on_catalog()
            self.info(f"Keyword changed from '{old_keyword}' to '{self._keyword}'")

        # Load CQL shortcuts
        self._cql_shortcuts = {}
        if settings.has_section("cqe_shortcuts"):
            for key in settings.keys("cqe_shortcuts"):
                cql_query = settings.get_stripped(
                    key, section="cqe_shortcuts", fallback=""
                )
                if cql_query:
                    # Store shortcuts in lowercase for case-insensitive matching
                    self._cql_shortcuts[key.lower()] = cql_query
            self.info(f"Loaded {len(self._cql_shortcuts)} CQL shortcuts")

        # Initialize Confluence client if credentials are available
        if self._is_configured():
            try:
                self.confluence_client = ConfluenceClient(
                    self.confluence_url, self.email, self.api_token
                )
                self.info("Confluence client initialized successfully")
            except Exception as e:
                self.err(f"Failed to initialize Confluence client: {str(e)}")
                self.confluence_client = None
        else:
            self.warn("Confluence credentials not configured")
            self.confluence_client = None

    def _filter_results(self, filter_text):
        """
        Filter cached results based on filter text

        Args:
            filter_text: Text to filter by (case-insensitive)

        Returns:
            List of filtered content items
        """
        if not self._cached_results:
            return []

        filter_lower = filter_text.lower()
        filtered = []

        for item in self._cached_results:
            # Search in: Title, Space Name, Type
            searchable_text = " ".join(
                [
                    item.get("title", ""),
                    item.get("space_name", ""),
                    item.get("type", ""),
                ]
            ).lower()

            if filter_lower in searchable_text:
                filtered.append(item)

        return filtered

    def _is_configured(self):
        """Check if all required configuration values are set"""
        return bool(self.confluence_url and self.email and self.api_token)

    def _generate_edit_url(self, page_url, page_id):
        """
        Generate edit URL from view URL

        Normal URL: <confluence-url>/wiki/spaces/FOO/pages/687210497/foobar-seite
        Edit URL: <confluence-url>/wiki/spaces/FOO/pages/edit-v2/687210497

        Args:
            page_url: Normal page URL
            page_id: Page ID

        Returns:
            Edit mode URL
        """
        # Extract base URL and space key from page URL
        # Pattern: <base>/wiki/spaces/<SPACE>/pages/<ID>/...
        match = re.match(r"(.*?/wiki/spaces/[^/]+)/pages/\d+", page_url)
        if match:
            base_path = match.group(1)
            edit_url = f"{base_path}/pages/edit-v2/{page_id}"
            return edit_url
        else:
            # Fallback: use page_url as-is
            self.warn(f"Could not parse URL for edit mode: {page_url}")
            return page_url

    def _handle_shortcut_input(self, user_input):
        """
        Handle shortcut input starting with #

        Args:
            user_input: User input string starting with #
        """
        shortcut_name = user_input[1:].lower()  # Remove # and lowercase

        suggestions = []

        # Show all shortcuts if only # is entered
        if shortcut_name == "":
            # Special shortcut: #edit
            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_SHORTCUT,
                    label="#edit",
                    short_desc="Open shortcuts configuration file",
                    target="edit_config",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                )
            )
            # Show all CQL shortcuts
            for name, cql in sorted(self._cql_shortcuts.items()):
                suggestions.append(
                    self.create_item(
                        category=self.ITEMCAT_SHORTCUT,
                        label=f"#{name}",
                        short_desc=cql,
                        target=f"shortcut_{name}",  # Unique target per shortcut
                        args_hint=kp.ItemArgsHint.ACCEPTED,  # Allow Enter to add to chain
                        hit_hint=kp.ItemHitHint.IGNORE,  # Reset hit hint
                        data_bag=cql,  # Store CQL for execution
                    )
                )
        else:
            # User typed something after # (e.g., "#me", "#m", "#o")
            # Check for EXACT match first - if found, show CQL execute item directly
            exact_match_cql = None
            if shortcut_name in self._cql_shortcuts:
                exact_match_cql = self._cql_shortcuts[shortcut_name]
                self.info(f"EXACT MATCH: #{shortcut_name} -> {exact_match_cql[:50]}...")
            elif shortcut_name == "edit":
                # Special case: #edit exact match
                self.info("EXACT MATCH: #edit -> open config")
                # Open config and return
                plugin_dir = os.path.dirname(__file__)
                config_path = os.path.join(
                    plugin_dir, "..", "..", "User", "keypi_cqe.ini"
                )
                config_path = os.path.abspath(config_path)
                suggestions.append(
                    self.create_item(
                        category=self.ITEMCAT_SHORTCUT,
                        label="#edit",
                        short_desc="Press Enter to open config file",
                        target="edit_config",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                    )
                )

            # If exact match found, show CQL execute item (like manual CQL input)
            if exact_match_cql:
                suggestions.append(
                    self.create_item(
                        category=self.ITEMCAT_QUERY,
                        label=f"{self._keyword}: {exact_match_cql}",
                        short_desc="Press Enter to execute query",
                        target="execute_cql",
                        args_hint=kp.ItemArgsHint.REQUIRED,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                        data_bag=exact_match_cql,
                    )
                )
            else:
                # No exact match - show prefix matches (shortcuts for further typing)
                # Check if "edit" matches as prefix
                if "edit".startswith(shortcut_name):
                    suggestions.append(
                        self.create_item(
                            category=self.ITEMCAT_SHORTCUT,
                            label="#edit",
                            short_desc="Open shortcuts configuration file",
                            target="edit_config",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.KEEPALL,
                        )
                    )

                # Check CQL shortcuts for prefix matches
                for name, cql in sorted(self._cql_shortcuts.items()):
                    if name.startswith(shortcut_name):
                        suggestions.append(
                            self.create_item(
                                category=self.ITEMCAT_SHORTCUT,
                                label=f"#{name}",
                                short_desc=cql,
                                target=f"shortcut_{name}",
                                args_hint=kp.ItemArgsHint.ACCEPTED,
                                hit_hint=kp.ItemHitHint.IGNORE,
                                data_bag=cql,
                            )
                        )

        if not suggestions:
            # No shortcuts found
            self.warn(f"No shortcuts matched: #{shortcut_name}")
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=f"{self._keyword}: #{shortcut_name}",
                    short_desc="No shortcuts found. Define shortcuts in keypi_cqe.ini",
                    target="no_shortcuts",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
