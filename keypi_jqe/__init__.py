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

from jira_client import JiraClient, JiraAuthError, JiraAPIError, JiraNetworkError


class JiraQueryExplorer(kp.Plugin):
    """
    Jira Query Explorer Plugin
    Allows querying Jira Cloud using JQL from Keypirinha
    """

    # Constants
    KEYWORD = "jqe"
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2

    def __init__(self):
        super().__init__()
        self.jira_client = None
        self.jira_url = None
        self.email = None
        self.api_token = None

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
                label=self.KEYWORD,
                short_desc="Query Jira using JQL",
                target=self.KEYWORD,
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.NOARGS
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
        # Only process if our keyword is in the chain
        if not items_chain or items_chain[0].category() != self.ITEMCAT_QUERY:
            return

        # Load configuration if not already loaded
        if not self.jira_client:
            self._load_config()

        # Check if configuration is valid
        if not self._is_configured():
            self.set_suggestions([
                self.create_error_item(
                    label="Configuration missing",
                    short_desc="Please configure your Jira credentials in keypi_jqe.ini"
                )
            ])
            return

        # If no JQL query entered yet, show hint
        if not user_input.strip():
            self.set_suggestions([
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label="Enter JQL query...",
                    short_desc="Example: assignee = currentUser() AND status = Open",
                    target="hint",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE
                )
            ])
            return

        # Execute JQL query
        jql_query = user_input.strip()
        self._execute_jql_query(jql_query)

    def _execute_jql_query(self, jql_query):
        """
        Execute JQL query and display results

        Args:
            jql_query: JQL query string
        """
        try:
            # Query Jira API
            issues = self.jira_client.search_issues(jql_query, max_results=50)

            if not issues:
                self.set_suggestions([
                    self.create_item(
                        category=kp.ItemCategory.KEYWORD,
                        label="No results found",
                        short_desc=f"No issues found for query: {jql_query}",
                        target="no_results",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE
                    )
                ])
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
                        target=issue['url'],
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                        data_bag=issue['key']
                    )
                )

            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

        except JiraAuthError as e:
            self.warn(str(e))
            self.set_suggestions([
                self.create_error_item(
                    label="Authentication failed",
                    short_desc=str(e)
                )
            ])

        except JiraAPIError as e:
            self.warn(str(e))
            self.set_suggestions([
                self.create_error_item(
                    label="API error",
                    short_desc=str(e)
                )
            ])

        except JiraNetworkError as e:
            self.warn(str(e))
            self.set_suggestions([
                self.create_error_item(
                    label="Network error",
                    short_desc=str(e)
                )
            ])

        except Exception as e:
            self.err(f"Unexpected error: {str(e)}")
            self.set_suggestions([
                self.create_error_item(
                    label="Unexpected error",
                    short_desc=f"An error occurred: {str(e)}"
                )
            ])

    def on_execute(self, item, action):
        """
        Execute action on selected item

        Args:
            item: Selected catalog item
            action: Action to execute
        """
        # Open Jira ticket URL in browser
        if item.category() == self.ITEMCAT_RESULT:
            url = item.target()
            kpu.shell_execute(url)

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
        self.jira_url = settings.get_stripped(
            "jira_url",
            section="main",
            fallback=""
        )

        self.email = settings.get_stripped(
            "atlassian_email",
            section="main",
            fallback=""
        )

        self.api_token = settings.get_stripped(
            "atlassian_api_key",
            section="main",
            fallback=""
        )

        # Initialize Jira client if credentials are available
        if self._is_configured():
            try:
                self.jira_client = JiraClient(
                    self.jira_url,
                    self.email,
                    self.api_token
                )
                self.info("Jira client initialized successfully")
            except Exception as e:
                self.err(f"Failed to initialize Jira client: {str(e)}")
                self.jira_client = None
        else:
            self.warn("Jira credentials not configured")
            self.jira_client = None

    def _is_configured(self):
        """Check if all required configuration values are set"""
        return bool(self.jira_url and self.email and self.api_token)
