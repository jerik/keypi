"""
Keypirinha Plugin: Jira Query Explorer (JQE)
Query Jira Cloud using JQL directly from Keypirinha launcher
"""

import keypirinha as kp
import keypirinha_util as kpu
import os
import sys
import json
from datetime import datetime
from urllib.parse import quote

# Add lib directory to path
_LIB_DIR = os.path.join(os.path.dirname(__file__), "lib")
sys.path.insert(0, _LIB_DIR)

from jira_client import JiraClient, JiraAuthError, JiraAPIError, JiraNetworkError  # noqa: E402


class JiraQueryExplorer(kp.Plugin):
    """
    Jira Query Explorer Plugin
    Allows querying Jira Cloud using JQL from Keypirinha
    """

    # Version
    VERSION = "1.4.0"

    # Constants
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_FILTER = kp.ItemCategory.USER_BASE + 3
    ITEMCAT_SHORTCUT = kp.ItemCategory.USER_BASE + 4
    ITEMCAT_HISTORY = kp.ItemCategory.USER_BASE + 5

    # History file name
    HISTORY_FILE = "keypi_jqe_history.json"
    HISTORY_VERSION = 1
    HISTORY_MAX_DEFAULT = 30

    # Modes
    MODE_JQL = "jql"
    MODE_FILTER = "filter"

    # Action names (for set_actions)
    ACTION_OPEN = "open"
    ACTION_COPY_URL = "copy_url"
    ACTION_COPY_JQL = "copy_jql"
    ACTION_OPEN_JQL_BROWSER = "open_jql_browser"

    def __init__(self):
        super().__init__()
        # Jira connection
        self.jira_client = None
        self.jira_url = None
        self.email = None
        self.api_token = None

        # State management for filter feature
        self._keyword = "jqe"  # Default keyword, configurable
        self._current_mode = self.MODE_JQL
        self._current_jql = ""
        self._cached_results = []
        self._filter_text = ""

        # JQL Shortcuts
        self._jql_shortcuts = {}  # {shortcut_name: jql_query}

        # History
        self._history_max_entries = self.HISTORY_MAX_DEFAULT

    def on_start(self):
        """Called when plugin is loaded"""
        self.info(f"JiraQueryExplorer v{self.VERSION} loaded")
        # Reset state to ensure clean start
        self._reset_to_jql_mode()

        # Register actions for result items
        self.set_actions(
            self.ITEMCAT_RESULT,
            [
                self.create_action(
                    name=self.ACTION_OPEN,
                    label="Open ticket",
                    short_desc="Open Jira ticket in browser (default)",
                ),
                self.create_action(
                    name=self.ACTION_COPY_URL,
                    label="Copy URL",
                    short_desc="Copy ticket URL to clipboard",
                ),
            ],
        )

        # Register actions for history items
        self.set_actions(
            self.ITEMCAT_HISTORY,
            [
                self.create_action(
                    name=self.ACTION_COPY_JQL,
                    label="Copy JQL",
                    short_desc="Copy JQL query to clipboard (default)",
                ),
                self.create_action(
                    name=self.ACTION_OPEN_JQL_BROWSER,
                    label="Open in browser",
                    short_desc="Open JQL search in Jira browser",
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
                short_desc="Query Jira using JQL",
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
            f"[on_suggest] user_input='{user_input}', mode={self._current_mode}, cached={len(self._cached_results)}, chain_len={len(items_chain) if items_chain else 0}"
        )

        # Only process if our keyword is in the chain
        if not items_chain or items_chain[0].category() != self.ITEMCAT_QUERY:
            return

        # Load configuration if not already loaded
        if not self.jira_client:
            self._load_config()

        # Check if configuration is valid
        if not self._is_configured():
            self.warn("Configuration missing - check keypi_jqe.ini")
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Configuration missing",
                        short_desc="Please configure your Jira credentials in keypi_jqe.ini",
                    )
                ]
            )
            return

        # IMPORTANT: Reset to JQL mode if user re-invokes keyword
        # This allows starting a new query even if stuck in FILTER mode
        if len(items_chain) == 1 and self._current_mode == self.MODE_FILTER:
            self.info("User re-invoked keyword - resetting to JQL mode for new query")
            self._reset_to_jql_mode()

        # Check if user pressed Tab on the "execute_jql" item
        # This happens when items_chain has 2 items: [keyword, execute_jql]
        # IMPORTANT: Only execute in JQL mode, not in FILTER mode!
        if (
            self._current_mode == self.MODE_JQL
            and len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_QUERY
            and items_chain[-1].target() == "execute_jql"
        ):
            jql_query = items_chain[-1].data_bag()
            self.dbg(f"Tab pressed on execute_jql in JQL mode: '{jql_query}'")
            self._execute_jql_query(jql_query)
            # After query execution, on_suggest will be called again
            # and we'll be in FILTER mode with cached results
            return

        # Check if user selected a shortcut (pressed Enter/Tab)
        # Show the expanded JQL as an "execute_jql" item (like manual JQL input)
        if (
            self._current_mode == self.MODE_JQL
            and len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target().startswith("shortcut_")
        ):
            jql_query = items_chain[-1].data_bag()
            shortcut_name = items_chain[-1].target().replace("shortcut_", "")
            self.info(
                f"Shortcut #{shortcut_name} selected, showing JQL: {jql_query[:50]}..."
            )

            # Show JQL as execute item (same as manual JQL input)
            # KEEPALL keeps Keypirinha open for Tab execution
            self.set_suggestions(
                [
                    self.create_item(
                        category=self.ITEMCAT_QUERY,
                        label=f"{self._keyword}: {jql_query}",
                        short_desc="Press Tab to execute query, or Esc to go back",
                        target="execute_jql",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                        data_bag=jql_query,
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
            config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_jqe.ini")
            config_path = os.path.abspath(config_path)
            self.info(f"Opening config file: {config_path}")
            kpu.shell_execute(config_path)
            self._reset_to_jql_mode()
            return

        # Check if user pressed Tab/Enter on #history
        # Show history entries
        if (
            len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target() == "show_history"
        ):
            self.info("Showing history entries")
            history = self._load_history()
            suggestions = []
            if history:
                for entry in history:
                    query = entry.get("query", "")
                    last_used = entry.get("last_used", "")[:10]  # Date only
                    suggestions.append(
                        self.create_item(
                            category=self.ITEMCAT_HISTORY,
                            label=query,
                            short_desc=f"Last used: {last_used}",
                            target="history_entry",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.KEEPALL,
                            data_bag=query,
                        )
                    )
            else:
                suggestions.append(
                    self.create_item(
                        category=kp.ItemCategory.KEYWORD,
                        label="No history entries",
                        short_desc="Execute some JQL queries to build history",
                        target="no_history",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                    )
                )
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
            return

        # Check if user pressed Tab/Enter on #history clear
        # Clear history and show confirmation
        if (
            len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target() == "clear_history"
        ):
            self._clear_history()
            self.set_suggestions(
                [
                    self.create_item(
                        category=kp.ItemCategory.KEYWORD,
                        label="History cleared",
                        short_desc="All history entries have been deleted",
                        target="history_cleared",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                    )
                ],
                kp.Match.ANY,
                kp.Sort.NONE,
            )
            return

        # Check if user selected a history entry
        # Show the JQL as an "execute_jql" item
        if (
            self._current_mode == self.MODE_JQL
            and len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_HISTORY
            and items_chain[-1].target().startswith("history_entry_")
        ):
            jql_query = items_chain[-1].data_bag()
            self.info(f"History entry selected, showing JQL: {jql_query[:50]}...")

            # Show JQL as execute item (same as manual JQL input)
            self.set_suggestions(
                [
                    self.create_item(
                        category=self.ITEMCAT_QUERY,
                        label=f"{self._keyword}: {jql_query}",
                        short_desc="Press Tab to execute query, or Esc to go back",
                        target="execute_jql",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                        data_bag=jql_query,
                    )
                ],
                kp.Match.ANY,
                kp.Sort.NONE,
            )
            return

        self.dbg(f"MODE={self._current_mode}, JQL='{self._current_jql}'")

        # State machine: Handle JQL mode vs Filter mode
        if self._current_mode == self.MODE_JQL:
            # JQL Input Mode - NO API calls during typing
            if not user_input.strip():
                # Show hint if no input
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="Enter JQL query or #shortcut...",
                            short_desc="Example: assignee = currentUser() | Use # for shortcuts",
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
                # User is typing JQL - show "Press Enter" hint (NO API call)
                self.dbg(f"JQL_MODE: typing '{user_input.strip()[:30]}...'")
                self.set_suggestions(
                    [
                        self.create_item(
                            category=self.ITEMCAT_QUERY,
                            label=f"{self._keyword}: {user_input.strip()}",
                            short_desc="Press Enter to execute query",
                            target="execute_jql",
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
                for issue in filtered_results:
                    label = f"{issue['key']}: [{issue['status']}] {issue['summary']}"
                    short_desc = (
                        f"Priority: {issue['priority']} | "
                        f"Assignee: {issue['assignee']} | "
                        f"Created: {issue['created'][:10]}"
                    )
                    suggestions.append(
                        self.create_item(
                            category=self.ITEMCAT_RESULT,
                            label=label,
                            short_desc=short_desc,
                            target=issue["url"],
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                            data_bag=json.dumps(issue),
                        )
                    )
                self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _execute_jql_query(self, jql_query):
        """
        Execute JQL query and cache results

        Args:
            jql_query: JQL query string
        """
        self.info(f"Executing JQL: {jql_query[:50]}...")
        try:
            # Query Jira API
            issues = self.jira_client.search_issues(jql_query, max_results=50)

            # Cache the JQL and results
            self._current_jql = jql_query
            self._cached_results = issues if issues else []

            # Switch to FILTER mode
            self._current_mode = self.MODE_FILTER
            self._filter_text = ""

            if not issues:
                self.info("Query returned 0 results")
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label=f"{self._keyword}: filter mode",
                            short_desc=f"No issues found for query: {jql_query[:50]}...",
                            target="no_results",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
                return

            # Create suggestion items from results
            suggestions = []
            for issue in issues:
                # Format: TICKET-ID: [Status] Summary
                label = f"{issue['key']}: [{issue['status']}] {issue['summary']}"

                # Additional info for description
                short_desc = (
                    f"Priority: {issue['priority']} | "
                    f"Assignee: {issue['assignee']} | "
                    f"Created: {issue['created'][:10]}"
                )

                suggestions.append(
                    self.create_item(
                        category=self.ITEMCAT_RESULT,
                        label=label,
                        short_desc=short_desc,
                        target=issue["url"],
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                        data_bag=json.dumps(issue),
                    )
                )

            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
            self.info(f"Query successful: {len(issues)} results cached")

            # Add to history after successful execution
            self._add_to_history(jql_query)

        except JiraAuthError as e:
            self.err(f"[_execute_jql_query] JiraAuthError: {str(e)}")
            self._current_mode = self.MODE_JQL
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Authentication failed", short_desc=str(e)
                    )
                ]
            )

        except JiraAPIError as e:
            self.err(f"[_execute_jql_query] JiraAPIError: {str(e)}")
            self._current_mode = self.MODE_JQL
            self.set_suggestions(
                [self.create_error_item(label="API error", short_desc=str(e))]
            )

        except JiraNetworkError as e:
            self.err(f"[_execute_jql_query] JiraNetworkError: {str(e)}")
            self._current_mode = self.MODE_JQL
            self.set_suggestions(
                [self.create_error_item(label="Network error", short_desc=str(e))]
            )

        except Exception as e:
            self.err(f"[_execute_jql_query] Unexpected error: {str(e)}")
            import traceback

            self.err(f"[_execute_jql_query] Traceback: {traceback.format_exc()}")
            self._current_mode = self.MODE_JQL
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
            action: Action to execute
        """
        # Handle JQL mode - Execute query when Enter is pressed (fallback)
        # NOTE: Tab is recommended (keeps Launchbox open), Enter closes it
        if item.category() == self.ITEMCAT_QUERY and item.target() == "execute_jql":
            jql_query = item.data_bag()
            self.info(f"Enter pressed - executing: {jql_query[:50]}...")
            self._execute_jql_query(jql_query)

        # Handle shortcut selection - Show JQL for review (not execute directly)
        # This allows user to see the query before executing with Tab
        elif item.category() == self.ITEMCAT_SHORTCUT and item.target().startswith(
            "shortcut_"
        ):
            jql_query = item.data_bag()
            shortcut_name = item.target().replace("shortcut_", "")
            self.info(
                f"Shortcut #{shortcut_name} selected via Enter, showing JQL: {jql_query[:50]}..."
            )

            # Show JQL as execute item (same as manual JQL input)
            # KEEPALL keeps Keypirinha open for Tab execution
            self.set_suggestions(
                [
                    self.create_item(
                        category=self.ITEMCAT_QUERY,
                        label=f"{self._keyword}: {jql_query}",
                        short_desc="Press Tab to execute query, or Esc to go back",
                        target="execute_jql",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                        data_bag=jql_query,
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
            # Plugin is in: Packages/keypi_jqe/
            # Config is in:  User/keypi_jqe.ini
            plugin_dir = os.path.dirname(__file__)
            config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_jqe.ini")
            config_path = os.path.abspath(config_path)
            self.info(f"Opening config file: {config_path}")
            # Open config file with default editor
            kpu.shell_execute(config_path)

        # Handle #history clear - Clear history
        elif (
            item.category() == self.ITEMCAT_SHORTCUT
            and item.target() == "clear_history"
        ):
            self._clear_history()
            self.info("History cleared via Enter")

        # Handle history entry selection with actions
        # Default: Copy JQL to clipboard
        # Alternative: Open JQL search in browser
        elif item.category() == self.ITEMCAT_HISTORY and item.target().startswith(
            "history_entry_"
        ):
            jql_query = item.data_bag()

            if not action or action.name() == self.ACTION_COPY_JQL:
                # Default action: Copy JQL to clipboard
                kpu.set_clipboard(jql_query)
                self.info(f"Copied JQL to clipboard: {jql_query[:50]}...")

            elif action.name() == self.ACTION_OPEN_JQL_BROWSER:
                # Open JQL search in Jira browser
                # URL format: <jira_url>/issues/?jql=<encoded_jql>
                encoded_jql = quote(jql_query, safe="")
                search_url = f"{self.jira_url}/issues/?jql={encoded_jql}"
                self.info(f"Opening JQL in browser: {jql_query[:50]}...")
                kpu.shell_execute(search_url)

        # Handle FILTER mode - Open Jira ticket URL in browser
        # Handle RESULT items with actions
        elif item.category() == self.ITEMCAT_RESULT:
            issue_data = json.loads(item.data_bag())
            ticket_url = item.target()
            ticket_key = issue_data["key"]

            if not action:
                # Default action (Enter): Open ticket
                self.info(f"Default action: Opening ticket {ticket_key}")
                kpu.shell_execute(ticket_url)
                self._reset_to_jql_mode()

            elif action.name() == self.ACTION_OPEN:
                # Open ticket action
                self.info(f"Action: Open ticket - {ticket_key}")
                kpu.shell_execute(ticket_url)
                self._reset_to_jql_mode()

            elif action.name() == self.ACTION_COPY_URL:
                # Copy URL to clipboard
                self.info(f"Action: Copy URL - {ticket_key}")
                kpu.set_clipboard(ticket_url)
                # Don't reset mode - user might want to copy multiple URLs

    def _reset_to_jql_mode(self):
        """Reset plugin state to JQL mode"""
        self.dbg(f"Resetting to JQL mode, clearing {len(self._cached_results)} results")
        self._current_mode = self.MODE_JQL
        self._current_jql = ""
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
        self.jira_url = settings.get_stripped("jira_url", section="main", fallback="")

        self.email = settings.get_stripped(
            "atlassian_email", section="main", fallback=""
        )

        self.api_token = settings.get_stripped(
            "atlassian_api_key", section="main", fallback=""
        )

        # Read keyword configuration (default: "jqe")
        old_keyword = self._keyword
        self._keyword = settings.get_stripped("keyword", section="main", fallback="jqe")

        # If keyword changed, update catalog
        if old_keyword != self._keyword:
            self.on_catalog()
            self.info(f"Keyword changed from '{old_keyword}' to '{self._keyword}'")

        # Load JQL shortcuts
        self._jql_shortcuts = {}
        if settings.has_section("jql_shortcuts"):
            for key in settings.keys("jql_shortcuts"):
                jql_query = settings.get_stripped(
                    key, section="jql_shortcuts", fallback=""
                )
                if jql_query:
                    # Store shortcuts in lowercase for case-insensitive matching
                    self._jql_shortcuts[key.lower()] = jql_query
            self.info(f"Loaded {len(self._jql_shortcuts)} JQL shortcuts")

        # Load history settings
        self._history_max_entries = settings.get_int(
            "history_max_entries",
            section="main",
            fallback=self.HISTORY_MAX_DEFAULT,
            min=1,
            max=1000,
        )
        self.info(f"History max entries: {self._history_max_entries}")

        # Initialize Jira client if credentials are available
        if self._is_configured():
            try:
                self.jira_client = JiraClient(self.jira_url, self.email, self.api_token)
                self.info("Jira client initialized successfully")
            except Exception as e:
                self.err(f"Failed to initialize Jira client: {str(e)}")
                self.jira_client = None
        else:
            self.warn("Jira credentials not configured")
            self.jira_client = None

    def _filter_results(self, filter_text):
        """
        Filter cached results based on filter text

        Args:
            filter_text: Text to filter by (case-insensitive)

        Returns:
            List of filtered issues
        """
        if not self._cached_results:
            return []

        filter_lower = filter_text.lower()
        filtered = []

        for issue in self._cached_results:
            # Search in: TicketID (key), Summary, Status
            searchable_text = " ".join(
                [
                    issue.get("key", ""),
                    issue.get("summary", ""),
                    issue.get("status", ""),
                ]
            ).lower()

            if filter_lower in searchable_text:
                filtered.append(issue)

        return filtered

    def _is_configured(self):
        """Check if all required configuration values are set"""
        return bool(self.jira_url and self.email and self.api_token)

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
            # Special shortcut: #history
            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_SHORTCUT,
                    label="#history",
                    short_desc="Show recent JQL queries",
                    target="show_history",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                )
            )
            # Special shortcut: #history clear
            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_SHORTCUT,
                    label="#history clear",
                    short_desc="Clear all history entries",
                    target="clear_history",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                )
            )
            # Show all JQL shortcuts
            for name, jql in sorted(self._jql_shortcuts.items()):
                suggestions.append(
                    self.create_item(
                        category=self.ITEMCAT_SHORTCUT,
                        label=f"#{name}",
                        short_desc=jql,
                        target=f"shortcut_{name}",  # Unique target per shortcut
                        args_hint=kp.ItemArgsHint.ACCEPTED,  # Allow Enter to add to chain
                        hit_hint=kp.ItemHitHint.IGNORE,  # Reset hit hint
                        data_bag=jql,  # Store JQL for execution
                    )
                )
        else:
            # User typed something after # (e.g., "#me", "#m", "#o")
            # Check for EXACT match first - if found, show JQL execute item directly
            exact_match_jql = None
            if shortcut_name in self._jql_shortcuts:
                exact_match_jql = self._jql_shortcuts[shortcut_name]
                self.info(f"EXACT MATCH: #{shortcut_name} -> {exact_match_jql[:50]}...")
            elif shortcut_name == "edit":
                # Special case: #edit exact match
                self.info("EXACT MATCH: #edit -> open config")
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
            elif shortcut_name in ("history", "his"):
                # Special case: #history exact match - show history entries
                self.info("EXACT MATCH: #history -> show history")
                history = self._load_history()
                self.info(f"[#history] Loaded {len(history)} history entries")
                if history:
                    for i, entry in enumerate(history):
                        query = entry.get("query", "")
                        last_used = entry.get("last_used", "")[:10]  # Date only
                        self.dbg(f"[#history] Entry {i}: {query[:30]}...")
                        # IMPORTANT: Each item needs unique target!
                        # Keypirinha deduplicates items with same target
                        suggestions.append(
                            self.create_item(
                                category=self.ITEMCAT_HISTORY,
                                label=query,
                                short_desc=f"Last used: {last_used}",
                                target=f"history_entry_{i}",
                                args_hint=kp.ItemArgsHint.ACCEPTED,
                                hit_hint=kp.ItemHitHint.IGNORE,
                                data_bag=query,
                            )
                        )
                    self.info(
                        f"[#history] Added {len(history)} history items to suggestions"
                    )
                else:
                    suggestions.append(
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="No history entries",
                            short_desc="Execute some JQL queries to build history",
                            target="no_history",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    )
            elif shortcut_name == "history clear":
                # Special case: #history clear exact match
                self.info("EXACT MATCH: #history clear -> clear history")
                suggestions.append(
                    self.create_item(
                        category=self.ITEMCAT_SHORTCUT,
                        label="#history clear",
                        short_desc="Press Enter to clear all history",
                        target="clear_history",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                    )
                )

            # If exact match found, show JQL execute item (like manual JQL input)
            if exact_match_jql:
                suggestions.append(
                    self.create_item(
                        category=self.ITEMCAT_QUERY,
                        label=f"{self._keyword}: {exact_match_jql}",
                        short_desc="Press Enter to execute query",
                        target="execute_jql",
                        args_hint=kp.ItemArgsHint.REQUIRED,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                        data_bag=exact_match_jql,
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

                # Check if "history" matches as prefix
                if "history".startswith(shortcut_name):
                    suggestions.append(
                        self.create_item(
                            category=self.ITEMCAT_SHORTCUT,
                            label="#history",
                            short_desc="Show recent JQL queries",
                            target="show_history",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.KEEPALL,
                        )
                    )

                # Check if "history clear" matches as prefix
                if "history clear".startswith(shortcut_name):
                    suggestions.append(
                        self.create_item(
                            category=self.ITEMCAT_SHORTCUT,
                            label="#history clear",
                            short_desc="Clear all history entries",
                            target="clear_history",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.KEEPALL,
                        )
                    )

                # Check JQL shortcuts for prefix matches
                for name, jql in sorted(self._jql_shortcuts.items()):
                    if name.startswith(shortcut_name):
                        suggestions.append(
                            self.create_item(
                                category=self.ITEMCAT_SHORTCUT,
                                label=f"#{name}",
                                short_desc=jql,
                                target=f"shortcut_{name}",
                                args_hint=kp.ItemArgsHint.ACCEPTED,
                                hit_hint=kp.ItemHitHint.IGNORE,
                                data_bag=jql,
                            )
                        )

        if not suggestions:
            # No shortcuts found
            self.warn(f"No shortcuts matched: #{shortcut_name}")
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=f"{self._keyword}: #{shortcut_name}",
                    short_desc="No shortcuts found. Define shortcuts in keypi_jqe.ini",
                    target="no_shortcuts",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.info(f"[_handle_shortcut_input] Setting {len(suggestions)} suggestions")
        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    # =========================================================================
    # History Methods
    # =========================================================================

    def _get_history_file_path(self):
        """
        Get the path to the history file

        Returns:
            Absolute path to history JSON file
        """
        # History file is stored in User directory (same as config)
        plugin_dir = os.path.dirname(__file__)
        user_dir = os.path.join(plugin_dir, "..", "..", "User")
        user_dir = os.path.abspath(user_dir)
        return os.path.join(user_dir, self.HISTORY_FILE)

    def _load_history(self):
        """
        Load history from JSON file

        Returns:
            List of history entries [{"query": "...", "last_used": "..."}]
        """
        history_path = self._get_history_file_path()
        self.dbg(f"[_load_history] Loading from: {history_path}")

        if not os.path.exists(history_path):
            self.dbg("[_load_history] File does not exist, returning empty list")
            return []

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate structure
            if not isinstance(data, dict) or "queries" not in data:
                self.warn("[_load_history] Invalid structure, resetting")
                return []

            queries = data.get("queries", [])
            self.dbg(f"[_load_history] Loaded {len(queries)} entries")
            return queries

        except json.JSONDecodeError as e:
            self.warn(f"[_load_history] Corrupted JSON, resetting: {e}")
            return []
        except Exception as e:
            self.warn(f"[_load_history] Error: {e}")
            return []

    def _save_history(self, queries):
        """
        Save history to JSON file

        Args:
            queries: List of history entries [{"query": "...", "last_used": "..."}]
        """
        history_path = self._get_history_file_path()
        self.dbg(f"[_save_history] Saving {len(queries)} entries to: {history_path}")

        data = {"version": self.HISTORY_VERSION, "queries": queries}

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(history_path), exist_ok=True)

            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.dbg("[_save_history] Saved successfully")

        except Exception as e:
            self.err(f"[_save_history] Error: {e}")

    def _add_to_history(self, query):
        """
        Add a query to history

        Args:
            query: JQL query string
        """
        if not query or not query.strip():
            self.dbg("[_add_to_history] Empty query, skipping")
            return

        query = query.strip()
        self.dbg(f"[_add_to_history] Adding: {query[:50]}...")

        queries = self._load_history()
        original_count = len(queries)

        # Remove duplicate if exists (case-insensitive comparison)
        query_lower = query.lower()
        queries = [q for q in queries if q.get("query", "").lower() != query_lower]
        removed_duplicate = len(queries) < original_count

        if removed_duplicate:
            self.dbg("[_add_to_history] Removed duplicate entry")

        # Add new entry at the beginning
        new_entry = {"query": query, "last_used": datetime.now().isoformat()}
        queries.insert(0, new_entry)

        # Trim to max entries
        queries = queries[: self._history_max_entries]

        self._save_history(queries)
        self.info(f"Added to history ({len(queries)} total): {query[:50]}...")

    def _clear_history(self):
        """Clear all history entries"""
        self._save_history([])
        self.info("History cleared")
