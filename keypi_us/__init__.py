"""
Keypirinha Plugin: User Search (US)
Search for users via Jira Cloud API
"""

import keypirinha as kp
import keypirinha_util as kpu
import os
import sys
import json

# Add lib directory to path
_LIB_DIR = os.path.join(os.path.dirname(__file__), "lib")
sys.path.insert(0, _LIB_DIR)

from user_client import UserClient, UserAuthError, UserAPIError, UserNetworkError  # noqa: E402


class UserSearch(kp.Plugin):
    """
    User Search Plugin
    Allows searching for users via Jira Cloud API from Keypirinha
    """

    # Version
    VERSION = "1.0.0"

    # Constants
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_RESULT_NO_EMAIL = kp.ItemCategory.USER_BASE + 3  # Users without email
    ITEMCAT_SHORTCUT = kp.ItemCategory.USER_BASE + 4  # For #edit etc.

    # Modes (state machine)
    MODE_SEARCH = "search"
    MODE_FILTER = "filter"

    # Action names
    ACTION_TEAMS_CHAT = "teams_chat"
    ACTION_OPEN_PROFILE = "open_profile"

    def __init__(self):
        super().__init__()
        # API connection
        self.user_client = None
        self.jira_url = None
        self.email = None
        self.api_token = None

        # Plugin settings
        self._keyword = "us"  # Default keyword, configurable

        # State management for filter feature
        self._current_mode = self.MODE_SEARCH
        self._current_query = ""
        self._cached_results = []
        self._filter_text = ""

    def on_start(self):
        """Called when plugin is loaded"""
        self.info(f"UserSearch v{self.VERSION} loaded")
        # Reset state to ensure clean start
        self._reset_to_search_mode()

        # Register actions for result items WITH email
        # Order: Open Profile first (for quick Tab access), Teams Chat is default (Enter)
        self.set_actions(
            self.ITEMCAT_RESULT,
            [
                self.create_action(
                    name=self.ACTION_OPEN_PROFILE,
                    label="Open Profile",
                    short_desc="Open user profile in browser",
                ),
                self.create_action(
                    name=self.ACTION_TEAMS_CHAT,
                    label="Teams Chat (default)",
                    short_desc="Open MS Teams chat with user",
                ),
            ],
        )

        # Register actions for result items WITHOUT email
        self.set_actions(
            self.ITEMCAT_RESULT_NO_EMAIL,
            [
                self.create_action(
                    name=self.ACTION_OPEN_PROFILE,
                    label="Open Profile (default)",
                    short_desc="Open user profile in browser",
                ),
                self.create_action(
                    name=self.ACTION_TEAMS_CHAT,
                    label="Teams Chat (nicht möglich - keine E-Mail)",
                    short_desc="E-Mail-Adresse nicht verfügbar",
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
                short_desc="Search for users",
                target=self._keyword,
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.NOARGS,
            )
        ]
        self.set_catalog(catalog)

    def on_suggest(self, user_input, items_chain):
        """
        Handle user input and provide suggestions

        State Machine:
        - MODE_SEARCH: User enters search term, Tab/Enter executes API search
        - MODE_FILTER: User filters cached results locally
        """
        # Only process if our keyword is in the chain
        if not items_chain or items_chain[0].category() != self.ITEMCAT_QUERY:
            return

        # Load configuration if not already loaded
        if not self.user_client:
            self._load_config()

        # Check if configuration is valid
        if not self._is_configured():
            self.warn("Configuration missing - check keypi_us.ini")
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Configuration missing",
                        short_desc="Please configure your Jira credentials in keypi_us.ini",
                    )
                ]
            )
            return

        # Reset to SEARCH mode if user re-invokes keyword (allows new search)
        if len(items_chain) == 1 and self._current_mode == self.MODE_FILTER:
            self.info("User re-invoked keyword - resetting to SEARCH mode")
            self._reset_to_search_mode()

        # Check if user pressed Tab on "execute_search" item
        # This happens when items_chain has 2 items: [keyword, execute_search]
        if (
            self._current_mode == self.MODE_SEARCH
            and len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_QUERY
            and items_chain[-1].target() == "execute_search"
        ):
            query = items_chain[-1].data_bag()
            self.dbg(f"Tab pressed on execute_search: '{query}'")
            self._execute_search(query)
            return

        # Check if user pressed Tab/Enter on #edit shortcut
        if (
            len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target() == "edit_config"
        ):
            plugin_dir = os.path.dirname(__file__)
            config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_us.ini")
            config_path = os.path.abspath(config_path)
            self.info(f"Opening config file: {config_path}")
            kpu.shell_execute(config_path)
            self._reset_to_search_mode()
            return

        # State machine: Handle SEARCH mode vs FILTER mode
        if self._current_mode == self.MODE_SEARCH:
            # SEARCH Input Mode - NO API calls during typing
            if not user_input.strip():
                # Show hint if no input
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="Enter search term...",
                            short_desc="Example: Max or max.mustermann | Use #edit for config",
                            target="hint",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
            elif user_input.strip().startswith("#"):
                # Shortcut mode - handle #edit
                self._handle_shortcut_input(user_input.strip())
            else:
                # User is typing - show "Press Tab to search" hint
                self.set_suggestions(
                    [
                        self.create_item(
                            category=self.ITEMCAT_QUERY,
                            label=f"{self._keyword}: {user_input.strip()}",
                            short_desc="Press Tab to search",
                            target="execute_search",
                            args_hint=kp.ItemArgsHint.REQUIRED,
                            hit_hint=kp.ItemHitHint.KEEPALL,
                            data_bag=user_input.strip(),
                        )
                    ]
                )

        elif self._current_mode == self.MODE_FILTER:
            # FILTER Mode - filter cached results locally
            filter_text = user_input.strip()
            self._filter_text = filter_text

            if not filter_text:
                # No filter - show all cached results
                filtered_results = self._cached_results
            else:
                # Filter cached results
                filtered_results = self._filter_results(filter_text)

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
                suggestions = self._build_user_suggestions(filtered_results)
                self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def on_execute(self, item, action):
        """
        Execute action on selected item
        """
        # Handle #edit shortcut
        if item.category() == self.ITEMCAT_SHORTCUT and item.target() == "edit_config":
            plugin_dir = os.path.dirname(__file__)
            config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_us.ini")
            config_path = os.path.abspath(config_path)
            self.info(f"Opening config file: {config_path}")
            kpu.shell_execute(config_path)
            return

        # Handle result item actions (with email)
        if item.category() == self.ITEMCAT_RESULT:
            user_data = json.loads(item.data_bag())
            email = user_data.get("email")
            profile_url = user_data.get("profile_url")

            if not action or action.name() == self.ACTION_TEAMS_CHAT:
                # Default action: Teams Chat
                teams_url = f"sip:{email}"
                self.info(f"Opening Teams chat: {teams_url}")
                kpu.shell_execute(teams_url)

            elif action.name() == self.ACTION_OPEN_PROFILE:
                self.info(f"Opening profile: {profile_url}")
                kpu.shell_execute(profile_url)

            self._reset_to_search_mode()

        # Handle result item actions (without email)
        elif item.category() == self.ITEMCAT_RESULT_NO_EMAIL:
            user_data = json.loads(item.data_bag())
            profile_url = user_data.get("profile_url")

            # Default action for no-email users: Open Profile
            if not action or action.name() == self.ACTION_OPEN_PROFILE:
                self.info(f"Opening profile: {profile_url}")
                kpu.shell_execute(profile_url)

            elif action.name() == self.ACTION_TEAMS_CHAT:
                # No email - do nothing, action label already says "nicht möglich"
                self.info("Teams Chat not possible - no email available")

            self._reset_to_search_mode()

    def _execute_search(self, query):
        """
        Execute user search and cache results
        """
        self.info(f"Searching users: '{query}'")

        try:
            # Search users via API
            users = self.user_client.search_users(query, max_results=50)

            # Cache query and results
            self._current_query = query
            self._cached_results = users if users else []

            # Switch to FILTER mode
            self._current_mode = self.MODE_FILTER
            self._filter_text = ""

            if not users:
                self.info("Search returned 0 results")
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label=f"{self._keyword}: filter mode",
                            short_desc=f"No users found for: {query}",
                            target="no_results",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
                return

            # Build and display suggestions
            suggestions = self._build_user_suggestions(users)
            self.info(f"Search returned {len(users)} users")
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

        except UserAuthError as e:
            self.err(f"Auth error: {e}")
            self._current_mode = self.MODE_SEARCH
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Authentication failed", short_desc=str(e)
                    )
                ]
            )

        except UserAPIError as e:
            self.err(f"API error: {e}")
            self._current_mode = self.MODE_SEARCH
            self.set_suggestions(
                [self.create_error_item(label="API error", short_desc=str(e))]
            )

        except UserNetworkError as e:
            self.err(f"Network error: {e}")
            self._current_mode = self.MODE_SEARCH
            self.set_suggestions(
                [self.create_error_item(label="Network error", short_desc=str(e))]
            )

        except Exception as e:
            self.err(f"Unexpected error: {e}")
            import traceback

            self.err(f"Traceback: {traceback.format_exc()}")
            self._current_mode = self.MODE_SEARCH
            self.set_suggestions(
                [self.create_error_item(label="Error", short_desc=str(e))]
            )

    def _build_user_suggestions(self, users):
        """
        Build suggestion items from user list

        Args:
            users: List of parsed user dictionaries

        Returns:
            List of catalog items
        """
        suggestions = []

        for user in users:
            display_name = user.get("display_name", "Unknown")
            email = user.get("email")
            active = user.get("active", False)
            account_type = user.get("account_type", "")

            # Build label and description based on email availability
            if email:
                label = f"{display_name} | {email}"
                short_desc = "Enter: Teams Chat | Tab+Enter: Profil"
                item_category = self.ITEMCAT_RESULT
            else:
                label = f"{display_name} | (keine E-Mail)"
                short_desc = "Enter: Profil öffnen"
                item_category = self.ITEMCAT_RESULT_NO_EMAIL

            # Add inactive/app indicator
            if not active:
                short_desc = f"[INACTIVE] {short_desc}"
            if account_type == "app":
                short_desc = f"[APP] {short_desc}"

            suggestions.append(
                self.create_item(
                    category=item_category,
                    label=label,
                    short_desc=short_desc,
                    target=user.get("profile_url", ""),
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    data_bag=json.dumps(user),
                )
            )

        return suggestions

    def _filter_results(self, filter_text):
        """
        Filter cached results based on filter text

        Args:
            filter_text: Text to filter by (case-insensitive)

        Returns:
            List of filtered users
        """
        if not self._cached_results:
            return []

        filter_lower = filter_text.lower()
        filtered = []

        for user in self._cached_results:
            # Search in: display_name, email
            searchable_text = " ".join(
                [
                    user.get("display_name", ""),
                    user.get("email", "") or "",
                ]
            ).lower()

            if filter_lower in searchable_text:
                filtered.append(user)

        return filtered

    def _reset_to_search_mode(self):
        """Reset plugin state to SEARCH mode"""
        self._current_mode = self.MODE_SEARCH
        self._current_query = ""
        self._cached_results = []
        self._filter_text = ""

    def _handle_shortcut_input(self, user_input):
        """
        Handle shortcut input starting with #

        Args:
            user_input: User input string starting with #
        """
        shortcut_name = user_input[1:].lower()  # Remove # and lowercase

        suggestions = []

        # Show #edit if matches
        if shortcut_name == "" or "edit".startswith(shortcut_name):
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
            # No shortcuts found
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=f"{self._keyword}: #{shortcut_name}",
                    short_desc="Unknown shortcut. Available: #edit",
                    target="no_shortcuts",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def on_events(self, flags):
        """Handle events (e.g., configuration changes)"""
        if flags & kp.Events.PACKCONFIG:
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

        # Read keyword configuration
        old_keyword = self._keyword
        self._keyword = settings.get_stripped("keyword", section="main", fallback="us")

        if old_keyword != self._keyword:
            self.on_catalog()
            self.info(f"Keyword changed from '{old_keyword}' to '{self._keyword}'")

        # Initialize client if configured
        if self._is_configured():
            try:
                self.user_client = UserClient(self.jira_url, self.email, self.api_token)
                self.info("User client initialized")
            except Exception as e:
                self.err(f"Failed to initialize client: {e}")
                self.user_client = None
        else:
            self.warn("Credentials not configured")
            self.user_client = None

    def _is_configured(self):
        """Check if all required configuration values are set"""
        return bool(self.jira_url and self.email and self.api_token)
