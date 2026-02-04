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

    # Version - increment with each commit during development
    VERSION = "1.0.0-dev.3"

    # Constants
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_RESULT_NO_EMAIL = kp.ItemCategory.USER_BASE + 3  # Users without email

    # Action names
    ACTION_TEAMS_CHAT = "teams_chat"
    ACTION_OPEN_PROFILE = "open_profile"

    # Debug response file
    DEBUG_RESPONSE_FILE = "keypi_us_debug_response.json"

    def __init__(self):
        super().__init__()
        # API connection
        self.user_client = None
        self.jira_url = None
        self.email = None
        self.api_token = None

        # Plugin settings
        self._keyword = "us"  # Default keyword, configurable

    def on_start(self):
        """Called when plugin is loaded"""
        self.info(f"UserSearch v{self.VERSION} loaded")

        # Register actions for result items WITH email
        self.set_actions(
            self.ITEMCAT_RESULT,
            [
                self.create_action(
                    name=self.ACTION_TEAMS_CHAT,
                    label="Teams Chat",
                    short_desc="Open MS Teams chat with user (default)",
                ),
                self.create_action(
                    name=self.ACTION_OPEN_PROFILE,
                    label="Open Profile",
                    short_desc="Open user profile in browser",
                ),
            ],
        )

        # Register actions for result items WITHOUT email
        self.set_actions(
            self.ITEMCAT_RESULT_NO_EMAIL,
            [
                self.create_action(
                    name=self.ACTION_OPEN_PROFILE,
                    label="Open Profile",
                    short_desc="Open user profile in browser (default)",
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
        """
        self.dbg(f"on_suggest: input='{user_input}', chain_len={len(items_chain)}")

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

        # Show hint if no input
        if not user_input.strip():
            self.set_suggestions(
                [
                    self.create_item(
                        category=kp.ItemCategory.KEYWORD,
                        label="Enter search term...",
                        short_desc="Example: Max or max.mustermann",
                        target="hint",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                    )
                ]
            )
            return

        # User is typing - show "Press Enter" hint
        # IMPORTANT: args_hint=FORBIDDEN allows Enter to execute (not require more input)
        self.dbg(f"Showing search item for query: '{user_input.strip()}'")
        self.set_suggestions(
            [
                self.create_item(
                    category=self.ITEMCAT_QUERY,
                    label=f"{self._keyword}: {user_input.strip()}",
                    short_desc="Press Enter to search",
                    target="execute_search",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                    data_bag=user_input.strip(),
                )
            ]
        )

    def on_execute(self, item, action):
        """
        Execute action on selected item
        """
        self.dbg(
            f"on_execute: cat={item.category()}, target='{item.target()}', "
            f"action={action.name() if action else 'None'}"
        )

        # Handle search execution
        if item.category() == self.ITEMCAT_QUERY and item.target() == "execute_search":
            query = item.data_bag()
            self.dbg(f"Executing search: '{query}'")
            self._execute_search(query)
            return

        # Handle result item actions (with email)
        if item.category() == self.ITEMCAT_RESULT:
            user_data = json.loads(item.data_bag())
            email = user_data.get("email")
            profile_url = user_data.get("profile_url")

            if not action or action.name() == self.ACTION_TEAMS_CHAT:
                # Default action: Teams Chat
                teams_url = f"sip:{email}"
                self.dbg(f"Opening Teams chat: {teams_url}")
                kpu.shell_execute(teams_url)

            elif action.name() == self.ACTION_OPEN_PROFILE:
                self.dbg(f"Opening profile: {profile_url}")
                kpu.shell_execute(profile_url)

        # Handle result item actions (without email)
        elif item.category() == self.ITEMCAT_RESULT_NO_EMAIL:
            user_data = json.loads(item.data_bag())
            profile_url = user_data.get("profile_url")

            # Default action for no-email users: Open Profile
            # Teams Chat action does nothing (no email available)
            if not action or action.name() == self.ACTION_OPEN_PROFILE:
                self.dbg(f"Opening profile: {profile_url}")
                kpu.shell_execute(profile_url)

            elif action.name() == self.ACTION_TEAMS_CHAT:
                # No email - do nothing, action label already says "nicht möglich"
                self.info("Teams Chat not possible - no email available")

    def _execute_search(self, query):
        """
        Execute user search and display results
        """
        self.info(f"Searching users: '{query}'")

        # Determine debug response file path
        plugin_dir = os.path.dirname(__file__)
        user_dir = os.path.join(plugin_dir, "..", "..", "User")
        user_dir = os.path.abspath(user_dir)
        debug_file = os.path.join(user_dir, self.DEBUG_RESPONSE_FILE)

        try:
            # Search users - save raw response for debugging
            users = self.user_client.search_users(
                query, max_results=50, save_raw_response_path=debug_file
            )
            self.info(f"Search returned {len(users)} users, saved to: {debug_file}")

            if not users:
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="No users found",
                            short_desc=f"No users match: {query}",
                            target="no_results",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
                return

            # Build suggestions from results
            suggestions = []
            users_with_email = 0
            users_without_email = 0

            for user in users:
                display_name = user.get("display_name", "Unknown")
                email = user.get("email")
                active = user.get("active", False)
                account_type = user.get("account_type", "")

                # Track email availability
                if email:
                    users_with_email += 1
                else:
                    users_without_email += 1

                # Build label and description based on email availability
                if email:
                    label = f"{display_name} | {email}"
                    short_desc = "Enter: Teams Chat | Tab: Actions"
                    item_category = self.ITEMCAT_RESULT
                else:
                    label = f"{display_name} | (keine E-Mail)"
                    short_desc = "Enter: Profil öffnen | Tab: Actions"
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

            self.info(
                f"Results: {len(users)} total, {users_with_email} with email, "
                f"{users_without_email} without email"
            )
            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

        except UserAuthError as e:
            self.err(f"Auth error: {e}")
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Authentication failed", short_desc=str(e)
                    )
                ]
            )

        except UserAPIError as e:
            self.err(f"API error: {e}")
            self.set_suggestions(
                [self.create_error_item(label="API error", short_desc=str(e))]
            )

        except UserNetworkError as e:
            self.err(f"Network error: {e}")
            self.set_suggestions(
                [self.create_error_item(label="Network error", short_desc=str(e))]
            )

        except Exception as e:
            self.err(f"Unexpected error: {e}")
            import traceback

            self.err(f"Traceback: {traceback.format_exc()}")
            self.set_suggestions(
                [self.create_error_item(label="Error", short_desc=str(e))]
            )

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
