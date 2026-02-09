"""
Keypirinha Plugin: Mindbox (MB)
Browse and open local Mindbox text files from Keypirinha launcher
"""

import keypirinha as kp
import keypirinha_util as kpu
import os
import time


class Mindbox(kp.Plugin):
    """
    Mindbox Plugin
    Lists .mb files from a configured folder and opens them with the default editor
    """

    # Version - increment with each commit during development
    VERSION = "1.0.0-dev.1"

    # Constants
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_SHORTCUT = kp.ItemCategory.USER_BASE + 3

    def __init__(self):
        super().__init__()
        # Plugin settings
        self._keyword = "mb"
        self._mindbox_folder = ""

        # Cached file list
        self._cached_files = []

    def on_start(self):
        """Called when plugin is loaded"""
        self.info(f"Mindbox v{self.VERSION} loaded")

    def on_catalog(self):
        """Populate the catalog with plugin items"""
        catalog = [
            self.create_item(
                category=self.ITEMCAT_QUERY,
                label=self._keyword,
                short_desc="Browse Mindbox files",
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

        # Load configuration if not yet loaded
        if not self._mindbox_folder:
            self._load_config()

        # Check if configuration is valid
        if not self._is_configured():
            self.warn("Configuration missing - check keypi_mindbox.ini")
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Configuration missing",
                        short_desc="Please set mindbox_folder in keypi_mindbox.ini",
                    )
                ]
            )
            return

        # Check if user pressed Tab/Enter on #edit
        if (
            len(items_chain) > 1
            and items_chain[-1].category() == self.ITEMCAT_SHORTCUT
            and items_chain[-1].target() == "edit_config"
        ):
            self._open_config_file()
            return

        # Handle #edit shortcut input
        if user_input.strip().startswith("#"):
            self._handle_shortcut_input(user_input.strip())
            return

        # Scan folder and build file list
        self._cached_files = self._scan_mindbox_folder()

        if not self._cached_files:
            self.set_suggestions(
                [
                    self.create_item(
                        category=kp.ItemCategory.KEYWORD,
                        label="No .mb files found",
                        short_desc=f"Folder: {self._mindbox_folder}",
                        target="no_files",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                    )
                ]
            )
            return

        # Build suggestions from file list
        suggestions = self._build_file_suggestions(self._cached_files)
        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def on_execute(self, item, action):
        """Execute action on selected item"""
        # Handle #edit shortcut
        if item.category() == self.ITEMCAT_SHORTCUT and item.target() == "edit_config":
            self._open_config_file()
            return

        # Handle file result - open with default editor
        if item.category() == self.ITEMCAT_RESULT:
            file_path = item.target()
            self.info(f"Opening file: {file_path}")
            kpu.shell_execute(file_path)

    def on_events(self, flags):
        """Handle events (e.g., configuration changes)"""
        if flags & kp.Events.PACKCONFIG:
            self._load_config()

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _load_config(self):
        """Load configuration from INI file"""
        settings = self.load_settings()

        self._mindbox_folder = settings.get_stripped(
            "mindbox_folder", section="main", fallback=""
        )

        old_keyword = self._keyword
        self._keyword = settings.get_stripped("keyword", section="main", fallback="mb")

        if old_keyword != self._keyword:
            self.on_catalog()
            self.info(f"Keyword changed from '{old_keyword}' to '{self._keyword}'")

        if self._mindbox_folder:
            self.info(f"Mindbox folder: {self._mindbox_folder}")
        else:
            self.warn("mindbox_folder not configured")

    def _is_configured(self):
        """Check if all required configuration values are set"""
        return bool(self._mindbox_folder)

    def _scan_mindbox_folder(self):
        """
        Scan the configured folder for .mb files

        Returns:
            List of dicts with file info: [{"name": "...", "path": "...", "modified": "..."}]
        """
        folder = self._mindbox_folder

        if not os.path.isdir(folder):
            self.warn(f"Mindbox folder does not exist: {folder}")
            return []

        files = []
        try:
            for entry in os.listdir(folder):
                if entry.lower().endswith(".mb"):
                    file_path = os.path.join(folder, entry)
                    if os.path.isfile(file_path):
                        mod_time = os.path.getmtime(file_path)
                        mod_date = time.strftime("%Y-%m-%d", time.localtime(mod_time))
                        name_without_ext = os.path.splitext(entry)[0]
                        files.append(
                            {
                                "name": name_without_ext,
                                "filename": entry,
                                "path": file_path,
                                "modified": mod_date,
                            }
                        )
        except OSError as e:
            self.err(f"Error scanning folder: {e}")
            return []

        # Sort by name (case-insensitive)
        files.sort(key=lambda f: f["name"].lower())
        return files

    def _build_file_suggestions(self, files):
        """
        Build suggestion items from file list

        Args:
            files: List of file info dicts

        Returns:
            List of Keypirinha items
        """
        suggestions = []

        for file_info in files:
            label = file_info["name"]
            short_desc = f"Modified: {file_info['modified']} | {file_info['filename']}"

            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_RESULT,
                    label=label,
                    short_desc=short_desc,
                    target=file_info["path"],
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        return suggestions

    def _handle_shortcut_input(self, user_input):
        """Handle shortcut input starting with #"""
        shortcut_input = user_input[1:].lower()  # Remove # and lowercase

        suggestions = []

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

        if not suggestions:
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=f"{self._keyword}: #{shortcut_input}",
                    short_desc="Unknown shortcut. Available: #edit",
                    target="no_shortcuts",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _open_config_file(self):
        """Open the configuration file"""
        plugin_dir = os.path.dirname(__file__)
        config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_mindbox.ini")
        config_path = os.path.abspath(config_path)
        self.info(f"Opening config file: {config_path}")
        kpu.shell_execute(config_path)
