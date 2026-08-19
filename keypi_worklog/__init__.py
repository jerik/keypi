"""
Keypirinha Plugin: WorkLog (WL)

Reads the Windows event log export, shows when the working day started and
appends the resulting working hours to a journal file.
"""

import json
import os
from datetime import datetime

import keypirinha as kp
import keypirinha_util as kpu

from .lib import worklog


class WorkLog(kp.Plugin):
    """
    WorkLog Plugin

    Workflow:
      1. Keyword "wl" lists the recent logon events (newest first)
      2. Tab on an entry shows the working time with the configured breaks
      3. Enter appends the selected variant to the journal file

    Shortcuts: #edit, #journal, #source
    Actions:   Write journal entry (default), Copy entry to clipboard
    """

    # Version - increment with each commit during development
    VERSION = "1.0.0-dev.1"

    # Item categories
    ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_SESSION = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_OPTION = kp.ItemCategory.USER_BASE + 3
    ITEMCAT_SHORTCUT = kp.ItemCategory.USER_BASE + 4

    # Actions on break variants
    ACTION_WRITE = "write_journal"
    ACTION_COPY = "copy_entry"

    # Documents folder, see KNOWNFOLDERID_Documents
    _DOCUMENTS_FOLDER_ID = "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"

    def __init__(self):
        super().__init__()
        self._keyword = "wl"
        self._winevent_log = ""
        self._journal_file = ""
        self._break_options = list(worklog.DEFAULT_BREAK_OPTIONS)
        self._rounding_minutes = worklog.DEFAULT_ROUNDING_MINUTES
        self._max_entries = worklog.DEFAULT_MAX_ENTRIES
        self._event_source = worklog.DEFAULT_SOURCE
        self._start_marker = worklog.DEFAULT_START_MARKER
        self._stop_marker = worklog.DEFAULT_STOP_MARKER
        self._journal_header = worklog.DEFAULT_JOURNAL_HEADER
        self._journal_entry = worklog.DEFAULT_JOURNAL_ENTRY
        self._config_loaded = False

    def on_start(self):
        """Called when the plugin is loaded"""
        self._load_config()
        self.set_actions(
            self.ITEMCAT_OPTION,
            [
                self.create_action(
                    name=self.ACTION_WRITE,
                    label="Write journal entry",
                    short_desc="Append the entry to the journal file",
                ),
                self.create_action(
                    name=self.ACTION_COPY,
                    label="Copy entry to clipboard",
                    short_desc="Copy the entry instead of writing it",
                ),
            ],
        )
        self.info(f"WorkLog v{self.VERSION} loaded")

    def on_catalog(self):
        """Register the keyword in the catalog"""
        self.set_catalog(
            [
                self.create_item(
                    category=self.ITEMCAT_QUERY,
                    label=self._keyword,
                    short_desc="Log working hours from the Windows event log",
                    target=self._keyword,
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.NOARGS,
                )
            ]
        )

    def on_suggest(self, user_input, items_chain):
        """Handle user input and provide suggestions"""
        if not items_chain or items_chain[0].category() != self.ITEMCAT_QUERY:
            return

        if not self._config_loaded:
            self._load_config()

        last = items_chain[-1]

        # Tab on a session entry: show the break variants
        if len(items_chain) > 1 and last.category() == self.ITEMCAT_SESSION:
            self._suggest_break_options(last)
            return

        # Tab on a shortcut behaves like Enter
        if len(items_chain) > 1 and last.category() == self.ITEMCAT_SHORTCUT:
            self._run_shortcut(last.target())
            return

        if user_input.strip().startswith("#"):
            self._suggest_shortcuts(user_input.strip())
            return

        self._suggest_sessions(user_input.strip())

    def on_execute(self, item, action):
        """Execute the selected item"""
        if item is None:
            return

        if item.category() == self.ITEMCAT_SHORTCUT:
            self._run_shortcut(item.target())
            return

        if item.category() == self.ITEMCAT_OPTION:
            self._execute_option(item, action)
            return

        if item.category() == self.ITEMCAT_SESSION:
            # Enter without Tab: nothing to write yet, keep the info at hand
            kpu.set_clipboard(f"{item.label()} {item.short_desc()}")
            self.info(f"Copied session info: {item.label()}")

    def on_events(self, flags):
        """Handle configuration changes"""
        if flags & kp.Events.PACKCONFIG:
            self._load_config()

    # =========================================================================
    # Configuration
    # =========================================================================

    def _default_logs_folder(self):
        """Documents\\logs, the folder both files live in by default"""
        try:
            documents = kpu.shell_known_folder_path(self._DOCUMENTS_FOLDER_ID)
        except Exception:
            return ""
        return os.path.join(documents, "logs")

    def _load_config(self):
        """Load the configuration from the INI file"""
        settings = self.load_settings()
        logs_folder = self._default_logs_folder()

        old_keyword = self._keyword
        self._keyword = settings.get_stripped("keyword", section="main", fallback="wl")

        self._winevent_log = settings.get_stripped(
            "winevent_log",
            section="main",
            fallback=os.path.join(logs_folder, "winevent.log") if logs_folder else "",
        )
        self._journal_file = settings.get_stripped(
            "journal_file",
            section="main",
            fallback=os.path.join(logs_folder, "Journal.log") if logs_folder else "",
        )

        self._break_options = worklog.parse_break_options(
            settings.get_stripped("break_options", section="main", fallback="")
        )
        self._rounding_minutes = worklog.parse_int_setting(
            settings.get_stripped("rounding_minutes", section="main", fallback=""),
            worklog.DEFAULT_ROUNDING_MINUTES,
            minimum=1,
            maximum=60,
        )
        self._max_entries = worklog.parse_int_setting(
            settings.get_stripped("max_entries", section="main", fallback=""),
            worklog.DEFAULT_MAX_ENTRIES,
            minimum=1,
            maximum=500,
        )

        self._event_source = settings.get_stripped(
            "event_source", section="main", fallback=worklog.DEFAULT_SOURCE
        )
        self._start_marker = settings.get_stripped(
            "event_start_marker", section="main", fallback=worklog.DEFAULT_START_MARKER
        )
        self._stop_marker = settings.get_stripped(
            "event_stop_marker", section="main", fallback=worklog.DEFAULT_STOP_MARKER
        )
        self._journal_header = settings.get_stripped(
            "journal_header", section="main", fallback=worklog.DEFAULT_JOURNAL_HEADER
        )
        self._journal_entry = settings.get_stripped(
            "journal_entry", section="main", fallback=worklog.DEFAULT_JOURNAL_ENTRY
        )

        self._config_loaded = True

        if old_keyword != self._keyword:
            self.on_catalog()
            self.info(f"Keyword changed from '{old_keyword}' to '{self._keyword}'")

        if not self._winevent_log:
            self.warn("winevent_log not configured")

    # =========================================================================
    # Suggestions
    # =========================================================================

    def _suggest_sessions(self, filter_text):
        """List the recent logon events"""
        if not self._winevent_log:
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Event log not configured",
                        short_desc="Set winevent_log in keypi_worklog.ini (#edit)",
                    )
                ]
            )
            return

        if not os.path.isfile(self._winevent_log):
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Event log not found",
                        short_desc=f"Path does not exist: {self._winevent_log}",
                    )
                ]
            )
            return

        now = datetime.now()
        try:
            sessions = worklog.load_sessions(
                self._winevent_log,
                now=now,
                max_entries=self._max_entries,
                source=self._event_source,
                start_marker=self._start_marker,
                stop_marker=self._stop_marker,
            )
        except OSError as error:
            self.err(f"Cannot read event log: {error}")
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Cannot read event log",
                        short_desc=str(error),
                    )
                ]
            )
            return

        if not sessions:
            self.set_suggestions(
                [
                    self.create_item(
                        category=kp.ItemCategory.KEYWORD,
                        label="No logon events found",
                        short_desc=f"Checked: {self._winevent_log}",
                        target="no_sessions",
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                    )
                ]
            )
            return

        suggestions = []
        needle = filter_text.lower()
        for session in sessions:
            described = worklog.describe_session(session, self._rounding_minutes)
            haystack = f"{described['label']} {described['description']}".lower()
            if needle and needle not in haystack:
                continue

            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_SESSION,
                    label=described["label"],
                    short_desc=described["description"],
                    target=worklog.session_key(session),
                    args_hint=kp.ItemArgsHint.ACCEPTED,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                    loop_on_suggest=True,
                    data_bag=json.dumps(
                        {
                            "start": session.start.isoformat(timespec="minutes"),
                            "end": None
                            if session.end is None
                            else session.end.isoformat(timespec="minutes"),
                            "running": session.running,
                        }
                    ),
                )
            )

        if not suggestions:
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label="No entry matches",
                    short_desc=f"No logon event matches: {filter_text}",
                    target="no_match",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _suggest_break_options(self, session_item):
        """Show the working time variants for the selected session"""
        session = self._session_from_item(session_item)
        if session is None:
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="Session no longer available",
                        short_desc="Please start over with the keyword",
                    )
                ]
            )
            return

        raw_minutes = worklog.session_minutes(session)
        if raw_minutes is None:
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="No logoff event for this session",
                        short_desc="The working time cannot be determined",
                    )
                ]
            )
            return

        day = session.start.date()
        rounded = worklog.round_minutes(raw_minutes, self._rounding_minutes)
        already_logged = worklog.find_journal_hours(
            self._journal_file, day, self._journal_entry
        )

        span = "{}-{}".format(
            session.start.strftime("%H:%M"), session.end.strftime("%H:%M")
        )

        suggestions = []
        for option in worklog.build_break_options(rounded, self._break_options):
            details = "{} · {} gerundet".format(span, worklog.format_duration(rounded))
            if option["break_minutes"]:
                details += " minus {}".format(
                    worklog.format_hours(option["break_minutes"])
                )
            if already_logged:
                details += " · ACHTUNG: bereits erfasst ({})".format(already_logged)

            suggestions.append(
                self.create_item(
                    category=self.ITEMCAT_OPTION,
                    label="{} · {}".format(option["hours"], option["break_label"]),
                    short_desc=details,
                    target="{}|{}".format(
                        worklog.session_key(session), option["break_minutes"]
                    ),
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    data_bag=json.dumps(
                        {
                            "date": day.strftime("%Y-%m-%d"),
                            "hours": option["hours"],
                        }
                    ),
                )
            )

        if not suggestions:
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label="Working time is shorter than every break",
                    short_desc="{} · {}".format(span, worklog.format_duration(rounded)),
                    target="no_options",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    def _suggest_shortcuts(self, user_input):
        """Show the # shortcuts"""
        needle = user_input[1:].lower()
        available = [
            ("#edit", "edit_config", "Open the configuration file"),
            (
                "#journal",
                "open_journal",
                f"Open {self._journal_file or 'journal file'}",
            ),
            ("#source", "open_source", f"Open {self._winevent_log or 'event log'}"),
        ]

        suggestions = [
            self.create_item(
                category=self.ITEMCAT_SHORTCUT,
                label=label,
                short_desc=description,
                target=target,
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.KEEPALL,
            )
            for label, target, description in available
            if not needle or label[1:].startswith(needle)
        ]

        if not suggestions:
            suggestions.append(
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=f"{self._keyword}: #{needle}",
                    short_desc="Unknown shortcut. Available: #edit, #journal, #source",
                    target="no_shortcut",
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                )
            )

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

    # =========================================================================
    # Execution
    # =========================================================================

    def _session_from_item(self, item):
        """Rebuild the session from the item data bag"""
        try:
            data = json.loads(item.data_bag() or "{}")
            start = datetime.fromisoformat(data["start"])
        except (ValueError, KeyError, TypeError):
            return None

        running = bool(data.get("running"))
        if running:
            end = datetime.now()
        elif data.get("end"):
            try:
                end = datetime.fromisoformat(data["end"])
            except ValueError:
                return None
        else:
            end = None

        return worklog.Session(start=start, end=end, running=running)

    def _execute_option(self, item, action):
        """Write or copy the journal entry"""
        try:
            data = json.loads(item.data_bag() or "{}")
            day = datetime.strptime(data["date"], "%Y-%m-%d").date()
            hours = data["hours"]
        except (ValueError, KeyError, TypeError) as error:
            self.err(f"Invalid item data: {error}")
            return

        text = worklog.render_journal_entry(
            day,
            datetime.now(),
            hours,
            header_template=self._journal_header,
            entry_template=self._journal_entry,
        )

        if action is not None and action.name() == self.ACTION_COPY:
            kpu.set_clipboard(text)
            self.info(f"Copied journal entry for {day}: {hours}")
            return

        if not self._journal_file:
            self.err("journal_file not configured")
            return

        try:
            worklog.append_journal_entry(self._journal_file, text)
        except OSError as error:
            self.err(f"Cannot write journal: {error}")
            return

        self.info(f"Wrote {hours} for {day} to {self._journal_file}")

    def _run_shortcut(self, target):
        """Open the file behind a shortcut"""
        if target == "edit_config":
            self._open_config_file()
            return

        if target == "open_journal":
            path = self._journal_file
        elif target == "open_source":
            path = self._winevent_log
        else:
            return

        if not path:
            self.warn(f"No path configured for {target}")
            return
        if not os.path.isfile(path):
            self.warn(f"File does not exist: {path}")
            return

        self.info(f"Opening file: {path}")
        kpu.shell_execute(path)

    def _open_config_file(self):
        """Open the plugin configuration file"""
        plugin_dir = os.path.dirname(__file__)
        config_path = os.path.abspath(
            os.path.join(plugin_dir, "..", "..", "User", "keypi_worklog.ini")
        )
        self.info(f"Opening config file: {config_path}")
        kpu.shell_execute(config_path)
