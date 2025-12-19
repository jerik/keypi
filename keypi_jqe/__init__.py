"""
Keypirinha Plugin: Jira Query Explorer (JQE)
Query Jira Cloud using JQL directly from Keypirinha launcher
"""

import keypirinha as kp
import keypirinha_util as kpu
import os
import sys

# Add lib directory to path
_LIB_DIR = os.path.join(os.path.dirname(__file__), "lib")
sys.path.insert(0, _LIB_DIR)

from jira_client import JiraClient, JiraAuthError, JiraAPIError, JiraNetworkError  # noqa: E402


class JiraQueryExplorer(kp.Plugin):
    """
    Jira Query Explorer Plugin
    Allows querying Jira Cloud using JQL from Keypirinha
    """

    # Constants
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_FILTER = kp.ItemCategory.USER_BASE + 3

    # Modes
    MODE_JQL = "jql"
    MODE_FILTER = "filter"

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

    def on_start(self):
        """Called when plugin is loaded"""
        pass

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
        self.info(
            f"[on_suggest] START - user_input='{user_input}', mode={self._current_mode}, cached={len(self._cached_results)} items"
        )

        # Only process if our keyword is in the chain
        if not items_chain or items_chain[0].category() != self.ITEMCAT_QUERY:
            self.info("[on_suggest] Not our keyword, returning")
            return

        # Load configuration if not already loaded
        if not self.jira_client:
            self.info("[on_suggest] Jira client not loaded, loading config...")
            self._load_config()

        # Check if configuration is valid
        if not self._is_configured():
            self.warn("[on_suggest] Configuration missing!")
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Configuration missing",
                        short_desc="Please configure your Jira credentials in keypi_jqe.ini",
                    )
                ]
            )
            return

        self.info(f"[on_suggest] MODE={self._current_mode}, JQL='{self._current_jql}'")

        # State machine: Handle JQL mode vs Filter mode
        if self._current_mode == self.MODE_JQL:
            self.info("[on_suggest] In JQL_MODE")
            # JQL Input Mode - NO API calls during typing
            if not user_input.strip():
                # Show hint if no input
                self.info("[on_suggest] JQL_MODE: Empty input, showing hint")
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="Enter JQL query...",
                            short_desc="Example: assignee = currentUser() AND status = Open",
                            target="hint",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
            else:
                # User is typing JQL - show "Press Enter" hint (NO API call)
                self.info(
                    f"[on_suggest] JQL_MODE: User typing JQL='{user_input.strip()}', NO API CALL"
                )
                self.set_suggestions(
                    [
                        self.create_item(
                            category=self.ITEMCAT_QUERY,
                            label=f"{self._keyword}: {user_input.strip()}",
                            short_desc="Press Enter to execute query",
                            target="execute_jql",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                            data_bag=user_input.strip(),
                        )
                    ]
                )

        elif self._current_mode == self.MODE_FILTER:
            self.info(
                f"[on_suggest] In FILTER_MODE - {len(self._cached_results)} cached results"
            )
            # Filter Mode - filter cached results locally
            filter_text = user_input.strip()
            self._filter_text = filter_text

            if not filter_text:
                # No filter - show all cached results
                self.info(
                    f"[on_suggest] FILTER_MODE: No filter text, showing all {len(self._cached_results)} results"
                )
                filtered_results = self._cached_results
            else:
                # Filter cached results
                self.info(
                    f"[on_suggest] FILTER_MODE: Filtering with text='{filter_text}'"
                )
                filtered_results = self._filter_results(filter_text)
                self.info(
                    f"[on_suggest] FILTER_MODE: Filtered to {len(filtered_results)} results"
                )

            if not filtered_results:
                self.info(
                    f"[on_suggest] FILTER_MODE: No matching results for filter='{filter_text}'"
                )
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="No matching results",
                            short_desc=f"No results match filter: {filter_text}",
                            target="no_results",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
            else:
                # Display filtered results
                self.info(
                    f"[on_suggest] FILTER_MODE: Displaying {len(filtered_results)} filtered results"
                )
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
                            data_bag=issue["key"],
                        )
                    )
                self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

        self.info("[on_suggest] END")

    def _execute_jql_query(self, jql_query):
        """
        Execute JQL query and cache results

        Args:
            jql_query: JQL query string
        """
        self.info(f"[_execute_jql_query] START - jql='{jql_query}'")
        try:
            # Query Jira API
            self.info("[_execute_jql_query] Calling Jira API...")
            issues = self.jira_client.search_issues(jql_query, max_results=50)
            self.info(
                f"[_execute_jql_query] API returned {len(issues) if issues else 0} issues"
            )

            # Cache the JQL and results
            self._current_jql = jql_query
            self._cached_results = issues if issues else []

            # Switch to FILTER mode
            old_mode = self._current_mode
            self._current_mode = self.MODE_FILTER
            self._filter_text = ""
            self.info(
                f"[_execute_jql_query] Mode switched: {old_mode} -> {self._current_mode}"
            )

            if not issues:
                self.info(
                    "[_execute_jql_query] No results found, showing error message"
                )
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="No results found",
                            short_desc=f"No issues found for query: {jql_query}",
                            target="no_results",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
                self.info("[_execute_jql_query] END - 0 results")
                return

            # Create suggestion items from results
            self.info(
                f"[_execute_jql_query] Creating {len(issues)} suggestion items..."
            )
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
                        data_bag=issue["key"],
                    )
                )

            self.info(f"[_execute_jql_query] Setting {len(suggestions)} suggestions")
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
            self.info(
                f"[_execute_jql_query] END - Success: {len(issues)} results cached"
            )

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
        self.info(
            f"[on_execute] START - item.category={item.category()}, item.target={item.target()}"
        )
        self.info(f"[on_execute] Current mode={self._current_mode}")

        # Handle JQL mode - Execute query when Enter is pressed
        if item.category() == self.ITEMCAT_QUERY and item.target() == "execute_jql":
            jql_query = item.data_bag()
            self.info(f"[on_execute] JQL mode - Executing query: '{jql_query}'")
            self._execute_jql_query(jql_query)
            self.info(f"[on_execute] Query executed, mode is now: {self._current_mode}")
            # REMOVED: self.set_suggestions([]) - This was closing the Launchbox!
            # The suggestions are already set by _execute_jql_query()

        # Handle FILTER mode - Open Jira ticket URL in browser
        elif item.category() == self.ITEMCAT_RESULT:
            url = item.target()
            ticket_key = item.data_bag()
            self.info(f"[on_execute] FILTER mode - Opening ticket {ticket_key}: {url}")
            kpu.shell_execute(url)
            # Reset to JQL mode after opening ticket
            self._reset_to_jql_mode()
            self.info(
                f"[on_execute] Ticket opened, reset to mode: {self._current_mode}"
            )
        else:
            self.warn(
                f"[on_execute] Unknown item category or target: {item.category()}/{item.target()}"
            )

        self.info("[on_execute] END")

    def _reset_to_jql_mode(self):
        """Reset plugin state to JQL mode"""
        self.info(
            f"[_reset_to_jql_mode] START - clearing {len(self._cached_results)} cached results"
        )
        self._current_mode = self.MODE_JQL
        self._current_jql = ""
        self._cached_results = []
        self._filter_text = ""
        self.info("[_reset_to_jql_mode] END - Reset to JQL mode complete")

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
        self.info(
            f"[_filter_results] START - filter_text='{filter_text}', cached={len(self._cached_results)}"
        )

        if not self._cached_results:
            self.info("[_filter_results] No cached results, returning empty list")
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

        self.info(f"[_filter_results] END - Found {len(filtered)} matching results")
        return filtered

    def _is_configured(self):
        """Check if all required configuration values are set"""
        return bool(self.jira_url and self.email and self.api_token)
