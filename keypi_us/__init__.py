"""
Keypirinha Plugin: User Search (US)
Search for users via Jira Cloud API
"""

import keypirinha as kp
import keypirinha_util as kpu
import os
import sys
import json
from datetime import datetime

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
    VERSION = "1.1.0"

    # Constants
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_RESULT_NO_EMAIL = kp.ItemCategory.USER_BASE + 3
    ITEMCAT_SHORTCUT = kp.ItemCategory.USER_BASE + 4
    ITEMCAT_HISTORY = kp.ItemCategory.USER_BASE + 5
    ITEMCAT_HISTORY_NO_EMAIL = kp.ItemCategory.USER_BASE + 6

    # History settings
    HISTORY_FILE = "keypi_us_history.json"
    HISTORY_VERSION = 1
    HISTORY_MAX_DEFAULT = 30

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
        self._keyword = "us"
        self._history_max_entries = self.HISTORY_MAX_DEFAULT

        # State management for filter feature
        self._current_mode = self.MODE_SEARCH
        self._current_query = ""
        self._cached_results = []
        self._filter_text = ""

    def on_start(self):
        """Called when plugin is loaded"""
        self.info(f"UserSearch v{self.VERSION} loaded")
        self._reset_to_search_mode()

        # Register actions for result items WITH email
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

        # Register actions for history items WITH email (same as result)
        self.set_actions(
            self.ITEMCAT_HISTORY,
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

        # Register actions for history items WITHOUT email
        self.set_actions(
            self.ITEMCAT_HISTORY_NO_EMAIL,
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
        """Populate the catalog with plugin items"""
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
        """Handle user input and provide suggestions"""
        if not items_chain or items_chain[0].category() != self.ITEMCAT_QUERY:
            return

        if not self.user_client:
            self._load_config()

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

        # Reset to SEARCH mode if user re-invokes keyword
        if len(items_chain) == 1 and self._current_mode == self.MODE_FILTER:
            self.info("User re-invoked keyword - resetting to SEARCH mode")
            self._reset_to_search_mode()

        # Check if user pressed Tab on "execute_search" item
        if (
            self._current_mode == self.MODE_SEARCH
            and len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_QUERY
            and items_chain[-1].target() == "execute_search"
        ):
            query = items_chain[-1].data_bag()
            self._execute_search(query)
            return

        # Check if user pressed Tab/Enter on #edit shortcut
        if (
            len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target() == "edit_config"
        ):
            self._open_config_file()
            return

        # Check if user selected #history show
        if (
            len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target() == "show_history"
        ):
            history = self._load_history()
            if not history:
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="History is empty",
                            short_desc="No users in history yet",
                            target="no_history",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
            else:
                suggestions = self._build_history_suggestions(history)
                self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
            return

        # Check if user selected #history clear
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
                ]
            )
            return

        # State machine: Handle SEARCH mode vs FILTER mode
        if self._current_mode == self.MODE_SEARCH:
            if not user_input.strip():
                # Show hint if no input
                self.set_suggestions(
                    [
                        self.create_item(
                            category=kp.ItemCategory.KEYWORD,
                            label="Enter search term...",
                            short_desc="Example: Max | Use #history, #edit",
                            target="hint",
                            args_hint=kp.ItemArgsHint.FORBIDDEN,
                            hit_hint=kp.ItemHitHint.IGNORE,
                        )
                    ]
                )
            elif user_input.strip().startswith("#"):
                # Shortcut mode
                self._handle_shortcut_input(user_input.strip())
            else:
                # User is typing - show filtered history + search option
                self._show_history_and_search_option(user_input.strip())

        elif self._current_mode == self.MODE_FILTER:
            # FILTER Mode - filter cached results locally
            filter_text = user_input.strip()
            self._filter_text = filter_text

            if not filter_text:
                filtered_results = self._cached_results
            else:
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
                suggestions = self._build_user_suggestions(filtered_results)
                self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _show_history_and_search_option(self, search_text):
        """
        Show filtered history entries + "Enter for API search" option

        Args:
            search_text: Current search text
        """
        suggestions = []

        # Filter history entries
        history = self._load_history()
        filtered_history = self._filter_history(history, search_text)

        # Add filtered history entries
        for i, user in enumerate(filtered_history):
            display_name = user.get("display_name", "Unknown")
            email = user.get("email")

            if email:
                label = f"[History] {display_name} | {email}"
                short_desc = "Enter: Teams Chat | Tab+Enter: Profil"
                item_category = self.ITEMCAT_HISTORY
            else:
                label = f"[History] {display_name} | (keine E-Mail)"
                short_desc = "Enter: Profil öffnen"
                item_category = self.ITEMCAT_HISTORY_NO_EMAIL

            suggestions.append(
                self.create_item(
                    category=item_category,
                    label=label,
                    short_desc=short_desc,
                    target=f"history_{i}",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    data_bag=json.dumps(user),
                )
            )

        # Always add "Enter for API search" option at the end
        suggestions.append(
            self.create_item(
                category=self.ITEMCAT_QUERY,
                label=f"{self._keyword}: {search_text}",
                short_desc="Tab/Enter: API-Suche starten",
                target="execute_search",
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.KEEPALL,
                data_bag=search_text,
            )
        )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def on_execute(self, item, action):
        """Execute action on selected item"""
        # Handle #edit shortcut
        if item.category() == self.ITEMCAT_SHORTCUT and item.target() == "edit_config":
            self._open_config_file()
            return

        # Handle #history clear
        if (
            item.category() == self.ITEMCAT_SHORTCUT
            and item.target() == "clear_history"
        ):
            self._clear_history()
            self.info("History cleared")
            return

        # Handle result item actions (with email)
        if item.category() == self.ITEMCAT_RESULT:
            user_data = json.loads(item.data_bag())
            self._execute_user_action(user_data, action)
            self._add_to_history(user_data)
            self._reset_to_search_mode()

        # Handle result item actions (without email)
        elif item.category() == self.ITEMCAT_RESULT_NO_EMAIL:
            user_data = json.loads(item.data_bag())
            self._execute_user_action_no_email(user_data, action)
            self._add_to_history(user_data)
            self._reset_to_search_mode()

        # Handle history item actions (with email)
        elif item.category() == self.ITEMCAT_HISTORY:
            user_data = json.loads(item.data_bag())
            self._execute_user_action(user_data, action)
            # Move to top of history
            self._add_to_history(user_data)

        # Handle history item actions (without email)
        elif item.category() == self.ITEMCAT_HISTORY_NO_EMAIL:
            user_data = json.loads(item.data_bag())
            self._execute_user_action_no_email(user_data, action)
            # Move to top of history
            self._add_to_history(user_data)

    def _execute_user_action(self, user_data, action):
        """Execute action for user with email"""
        email = user_data.get("email")
        profile_url = user_data.get("profile_url")

        if not action or action.name() == self.ACTION_TEAMS_CHAT:
            teams_url = f"sip:{email}"
            self.info(f"Opening Teams chat: {teams_url}")
            kpu.shell_execute(teams_url)
        elif action.name() == self.ACTION_OPEN_PROFILE:
            self.info(f"Opening profile: {profile_url}")
            kpu.shell_execute(profile_url)

    def _execute_user_action_no_email(self, user_data, action):
        """Execute action for user without email"""
        profile_url = user_data.get("profile_url")

        if not action or action.name() == self.ACTION_OPEN_PROFILE:
            self.info(f"Opening profile: {profile_url}")
            kpu.shell_execute(profile_url)
        elif action.name() == self.ACTION_TEAMS_CHAT:
            self.info("Teams Chat not possible - no email available")

    def _open_config_file(self):
        """Open the configuration file"""
        plugin_dir = os.path.dirname(__file__)
        config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_us.ini")
        config_path = os.path.abspath(config_path)
        self.info(f"Opening config file: {config_path}")
        kpu.shell_execute(config_path)

    def _execute_search(self, query):
        """Execute user search and cache results"""
        self.info(f"Searching users: '{query}'")

        try:
            users = self.user_client.search_users(query, max_results=50)
            self._current_query = query
            self._cached_results = users if users else []
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
        """Build suggestion items from user list"""
        suggestions = []

        for user in users:
            display_name = user.get("display_name", "Unknown")
            email = user.get("email")
            active = user.get("active", False)
            account_type = user.get("account_type", "")

            if email:
                label = f"{display_name} | {email}"
                short_desc = "Enter: Teams Chat | Tab+Enter: Profil"
                item_category = self.ITEMCAT_RESULT
            else:
                label = f"{display_name} | (keine E-Mail)"
                short_desc = "Enter: Profil öffnen"
                item_category = self.ITEMCAT_RESULT_NO_EMAIL

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

    def _build_history_suggestions(self, history):
        """Build suggestion items from history"""
        suggestions = []

        for i, user in enumerate(history):
            display_name = user.get("display_name", "Unknown")
            email = user.get("email")
            last_used = user.get("last_used", "")

            if last_used:
                last_used_short = last_used[:10]  # YYYY-MM-DD
            else:
                last_used_short = "N/A"

            if email:
                label = f"{display_name} | {email}"
                short_desc = f"Last used: {last_used_short} | Enter: Teams Chat"
                item_category = self.ITEMCAT_HISTORY
            else:
                label = f"{display_name} | (keine E-Mail)"
                short_desc = f"Last used: {last_used_short} | Enter: Profil"
                item_category = self.ITEMCAT_HISTORY_NO_EMAIL

            suggestions.append(
                self.create_item(
                    category=item_category,
                    label=label,
                    short_desc=short_desc,
                    target=f"history_{i}",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    data_bag=json.dumps(user),
                )
            )

        return suggestions

    def _filter_results(self, filter_text):
        """Filter cached results based on filter text"""
        if not self._cached_results:
            return []

        filter_lower = filter_text.lower()
        filtered = []

        for user in self._cached_results:
            searchable_text = " ".join(
                [
                    user.get("display_name", ""),
                    user.get("email", "") or "",
                ]
            ).lower()

            if filter_lower in searchable_text:
                filtered.append(user)

        return filtered

    def _filter_history(self, history, filter_text):
        """Filter history entries based on filter text"""
        if not history:
            return []

        filter_lower = filter_text.lower()
        filtered = []

        for user in history:
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
        """Handle shortcut input starting with #"""
        shortcut_input = user_input[1:].lower()  # Remove # and lowercase

        suggestions = []

        # Check for #history clear
        if shortcut_input.startswith("history") and " " in user_input:
            rest = user_input.split(" ", 1)[1].lower() if " " in user_input else ""
            if "clear".startswith(rest) or rest == "clear":
                suggestions.append(
                    self.create_item(
                        category=self.ITEMCAT_SHORTCUT,
                        label="#history clear",
                        short_desc="Delete all history entries",
                        target="clear_history",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.KEEPALL,
                    )
                )
                self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
                return

        # Show #edit if matches
        if shortcut_input == "" or "edit".startswith(shortcut_input):
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

        # Show #history if matches
        if shortcut_input == "" or "history".startswith(shortcut_input):
            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_SHORTCUT,
                    label="#history",
                    short_desc="Show all history entries (Tab to show)",
                    target="show_history",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.NOARGS,
                )
            )

        # Show #history clear if matches
        if shortcut_input == "" or "history".startswith(shortcut_input):
            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_SHORTCUT,
                    label="#history clear",
                    short_desc="Delete all history entries",
                    target="clear_history",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                )
            )

        if not suggestions:
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=f"{self._keyword}: #{shortcut_input}",
                    short_desc="Unknown shortcut. Available: #edit, #history",
                    target="no_shortcuts",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    # =========================================================================
    # History Methods
    # =========================================================================

    def _get_history_file_path(self):
        """Get the path to the history file"""
        plugin_dir = os.path.dirname(__file__)
        user_dir = os.path.join(plugin_dir, "..", "..", "User")
        user_dir = os.path.abspath(user_dir)
        return os.path.join(user_dir, self.HISTORY_FILE)

    def _load_history(self):
        """Load history from JSON file"""
        history_path = self._get_history_file_path()

        if not os.path.exists(history_path):
            return []

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or "users" not in data:
                self.warn("[_load_history] Invalid structure, resetting")
                return []

            users = data.get("users", [])
            return users

        except json.JSONDecodeError as e:
            self.warn(f"[_load_history] Corrupted JSON, resetting: {e}")
            return []
        except Exception as e:
            self.warn(f"[_load_history] Error: {e}")
            return []

    def _save_history(self, users):
        """Save history to JSON file"""
        history_path = self._get_history_file_path()

        data = {"version": self.HISTORY_VERSION, "users": users}

        try:
            os.makedirs(os.path.dirname(history_path), exist_ok=True)

            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.err(f"[_save_history] Error: {e}")

    def _add_to_history(self, user):
        """Add a user to history"""
        if not user or not user.get("account_id"):
            return

        account_id = user.get("account_id")

        users = self._load_history()
        original_count = len(users)

        # Remove duplicate if exists (by account_id)
        users = [u for u in users if u.get("account_id") != account_id]
        removed_duplicate = len(users) < original_count

        # Add new entry at the beginning with timestamp
        new_entry = {
            "account_id": user.get("account_id"),
            "display_name": user.get("display_name"),
            "email": user.get("email"),
            "profile_url": user.get("profile_url"),
            "active": user.get("active", True),
            "account_type": user.get("account_type", "atlassian"),
            "last_used": datetime.now().isoformat(),
        }
        users.insert(0, new_entry)

        # Trim to max entries
        users = users[: self._history_max_entries]

        self._save_history(users)

        display_name = user.get("display_name", "Unknown")
        if removed_duplicate:
            self.info(f"Moved to top of history: {display_name}")
        else:
            self.info(f"Added to history ({len(users)} total): {display_name}")

    def _clear_history(self):
        """Clear all history entries"""
        self._save_history([])
        self.info("History cleared")

    # =========================================================================
    # Config & Events
    # =========================================================================

    def on_events(self, flags):
        """Handle events (e.g., configuration changes)"""
        if flags & kp.Events.PACKCONFIG:
            self._load_config()

    def _load_config(self):
        """Load configuration from INI file"""
        settings = self.load_settings()

        self.jira_url = settings.get_stripped("jira_url", section="main", fallback="")
        self.email = settings.get_stripped(
            "atlassian_email", section="main", fallback=""
        )
        self.api_token = settings.get_stripped(
            "atlassian_api_key", section="main", fallback=""
        )

        old_keyword = self._keyword
        self._keyword = settings.get_stripped("keyword", section="main", fallback="us")

        if old_keyword != self._keyword:
            self.on_catalog()
            self.info(f"Keyword changed from '{old_keyword}' to '{self._keyword}'")

        # Load history settings
        self._history_max_entries = settings.get_int(
            "history_max_entries",
            section="main",
            fallback=self.HISTORY_MAX_DEFAULT,
            min=1,
            max=100,
        )

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
