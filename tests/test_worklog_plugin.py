"""
Integration tests for the WorkLog plugin class.

Keypirinha is only available inside the launcher, so this module installs a
minimal stub of the keypirinha API before importing the plugin. That way the
state machine (keyword -> session list -> break variants -> journal entry) is
covered without a Windows installation.
"""

import os
import sys
import tempfile
import types
import unittest
from datetime import date, datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "winevent_sample.log")


# ---------------------------------------------------------------------------
# Keypirinha API stub
# ---------------------------------------------------------------------------


class _Item:
    """Stand-in for keypirinha.CatalogItem"""

    def __init__(self, category, label, short_desc, target, data_bag="", **kwargs):
        self._category = category
        self._label = label
        self._short_desc = short_desc
        self._target = target
        self._data_bag = data_bag
        self.hints = kwargs

    def category(self):
        return self._category

    def label(self):
        return self._label

    def short_desc(self):
        return self._short_desc

    def target(self):
        return self._target

    def data_bag(self):
        return self._data_bag


class _Action:
    def __init__(self, name, label="", short_desc=""):
        self._name = name
        self._label = label

    def name(self):
        return self._name


class _Settings:
    """Stand-in for keypirinha.settings.Settings"""

    def __init__(self, values=None):
        self.values = values or {}

    def get_stripped(self, key, section="main", fallback=""):
        value = self.values.get(key)
        if value is None or value == "":
            return fallback
        return value.strip()


class _Plugin:
    """Stand-in for keypirinha.plugin.Plugin"""

    def __init__(self):
        self.settings = _Settings()
        self.catalog = []
        self.suggestions = []
        self.actions = {}
        self.messages = []

    def load_settings(self):
        return self.settings

    def set_catalog(self, catalog):
        self.catalog = catalog

    def set_suggestions(self, suggestions, match=None, sort=None):
        self.suggestions = suggestions

    def set_actions(self, category, actions):
        self.actions[category] = actions

    def create_item(self, category, label, short_desc, target, data_bag="", **kwargs):
        return _Item(category, label, short_desc, target, data_bag, **kwargs)

    def create_error_item(self, label, short_desc, **kwargs):
        return _Item("error", label, short_desc, "error")

    def create_action(self, name, label="", short_desc=""):
        return _Action(name, label, short_desc)

    def info(self, *args):
        self.messages.append(("info", " ".join(str(arg) for arg in args)))

    def warn(self, *args):
        self.messages.append(("warn", " ".join(str(arg) for arg in args)))

    def err(self, *args):
        self.messages.append(("err", " ".join(str(arg) for arg in args)))


def _install_stubs():
    """
    Register fake keypirinha modules so the plugin can be imported.

    Other test modules install their own minimal stub. This one is a superset
    of those, so it always replaces what is already registered.
    """
    kp = types.ModuleType("keypirinha")
    kp.Plugin = _Plugin
    kp.ItemCategory = types.SimpleNamespace(USER_BASE=100, KEYWORD=1)
    kp.ItemArgsHint = types.SimpleNamespace(REQUIRED=1, FORBIDDEN=2, ACCEPTED=3)
    kp.ItemHitHint = types.SimpleNamespace(NOARGS=1, IGNORE=2, KEEPALL=3)
    kp.Match = types.SimpleNamespace(ANY=1, DEFAULT=2, FUZZY=3)
    kp.Sort = types.SimpleNamespace(NONE=1, SCORE_DESC=2)
    kp.Events = types.SimpleNamespace(PACKCONFIG=1)

    kpu = types.ModuleType("keypirinha_util")
    kpu.clipboard = []
    kpu.executed = []
    kpu.documents = tempfile.mkdtemp()

    def shell_known_folder_path(folder_id):
        return kpu.documents

    def shell_execute(path):
        kpu.executed.append(path)

    def set_clipboard(text):
        kpu.clipboard.append(text)

    kpu.shell_known_folder_path = shell_known_folder_path
    kpu.shell_execute = shell_execute
    kpu.set_clipboard = set_clipboard

    sys.modules["keypirinha"] = kp
    sys.modules["keypirinha_util"] = kpu


_install_stubs()

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import keypirinha_util as kpu_stub  # noqa: E402
from keypi_worklog import WorkLog  # noqa: E402


class _PluginTestCase(unittest.TestCase):
    """Shared setup: a configured plugin instance on a temp journal"""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.journal = os.path.join(self.folder, "Journal.log")
        self.plugin = WorkLog()
        self.plugin.settings = _Settings(
            {
                "winevent_log": FIXTURE,
                "journal_file": self.journal,
            }
        )
        self.plugin.on_start()
        del kpu_stub.clipboard[:]
        del kpu_stub.executed[:]

    def keyword_item(self):
        return _Item(WorkLog.ITEMCAT_QUERY, "wl", "", "wl")

    def session_items(self, user_input=""):
        self.plugin.on_suggest(user_input, [self.keyword_item()])
        return self.plugin.suggestions

    def option_items(self, session_item):
        self.plugin.on_suggest("", [self.keyword_item(), session_item])
        return self.plugin.suggestions

    def read_journal(self):
        with open(self.journal, encoding="utf-8") as handle:
            return handle.read()


class TestCatalogAndConfig(_PluginTestCase):
    def test_catalog_uses_configured_keyword(self):
        self.plugin.on_catalog()
        self.assertEqual(1, len(self.plugin.catalog))
        self.assertEqual("wl", self.plugin.catalog[0].label())

    def test_custom_keyword(self):
        self.plugin.settings.values["keyword"] = "zeit"
        self.plugin.on_events(1)
        self.assertEqual("zeit", self.plugin.catalog[0].label())

    def test_defaults_point_into_the_documents_folder(self):
        plugin = WorkLog()
        plugin.settings = _Settings()
        plugin.on_start()
        self.assertTrue(plugin._winevent_log.endswith("winevent.log"))
        self.assertTrue(plugin._journal_file.endswith("Journal.log"))

    def test_invalid_settings_fall_back(self):
        self.plugin.settings.values.update(
            {"break_options": "abc", "rounding_minutes": "0", "max_entries": "-1"}
        )
        self.plugin.on_events(1)
        self.assertEqual([0, 60, 90], self.plugin._break_options)
        self.assertEqual(15, self.plugin._rounding_minutes)
        self.assertEqual(30, self.plugin._max_entries)

    def test_actions_are_registered_for_break_variants(self):
        actions = self.plugin.actions[WorkLog.ITEMCAT_OPTION]
        self.assertEqual(
            [WorkLog.ACTION_WRITE, WorkLog.ACTION_COPY],
            [action.name() for action in actions],
        )

    def test_no_actions_on_session_items(self):
        """Actions would take priority over Tab chaining"""
        self.assertNotIn(WorkLog.ITEMCAT_SESSION, self.plugin.actions)


class TestSessionSuggestions(_PluginTestCase):
    def test_lists_sessions_newest_first(self):
        items = self.session_items()
        self.assertTrue(items)
        self.assertEqual(WorkLog.ITEMCAT_SESSION, items[0].category())
        self.assertEqual("2026-01-05T08:12", items[0].target())

    def test_session_items_are_chainable(self):
        hints = self.session_items()[0].hints
        self.assertEqual(3, hints["args_hint"])  # ACCEPTED
        self.assertEqual(3, hints["hit_hint"])  # KEEPALL
        self.assertTrue(hints["loop_on_suggest"])

    def test_targets_are_unique(self):
        targets = [item.target() for item in self.session_items()]
        self.assertEqual(len(targets), len(set(targets)))

    def test_filter_by_user_input(self):
        items = self.session_items("2025-12-22")
        self.assertTrue(items)
        for item in items:
            self.assertIn("2025-12-22", item.short_desc())

    def test_filter_without_match(self):
        items = self.session_items("1999")
        self.assertEqual(1, len(items))
        self.assertEqual("No entry matches", items[0].label())

    def test_max_entries_is_applied(self):
        self.plugin.settings.values["max_entries"] = "2"
        self.plugin.on_events(1)
        self.assertEqual(2, len(self.session_items()))

    def test_missing_event_log_shows_error(self):
        self.plugin.settings.values["winevent_log"] = os.path.join(
            self.folder, "missing.log"
        )
        self.plugin.on_events(1)
        items = self.session_items()
        self.assertEqual("Event log not found", items[0].label())

    def test_ignores_other_plugins_item_chains(self):
        self.plugin.suggestions = []
        self.plugin.on_suggest("", [_Item(999, "other", "", "other")])
        self.assertEqual([], self.plugin.suggestions)


class TestBreakOptions(_PluginTestCase):
    def test_options_for_a_closed_session(self):
        session = [
            item for item in self.session_items() if item.target() == "2026-01-02T08:05"
        ][0]
        options = self.option_items(session)

        # 08:05 to 17:30 is 9h25m, rounded 9h30m
        self.assertEqual(
            ["9,5h · ohne Pause", "8,5h · 1h Pause", "8h · 1,5h Pause"],
            [item.label() for item in options],
        )
        self.assertEqual(WorkLog.ITEMCAT_OPTION, options[0].category())

    def test_option_targets_are_unique(self):
        session = self.session_items()[0]
        targets = [item.target() for item in self.option_items(session)]
        self.assertEqual(len(targets), len(set(targets)))

    def test_running_session_uses_the_current_time(self):
        session = self.session_items()[0]
        options = self.option_items(session)
        self.assertTrue(options)
        self.assertIn("08:12", options[0].short_desc())

    def test_short_session_drops_impossible_breaks(self):
        session = [
            item for item in self.session_items() if item.target() == "2025-12-29T23:43"
        ][0]
        options = self.option_items(session)
        # 23:43 to 01:06 is 1h23m, rounded 1h30m: the 1,5h break leaves nothing
        self.assertEqual(
            ["1,5h · ohne Pause", "0,5h · 1h Pause"],
            [item.label() for item in options],
        )

    def test_warns_when_the_day_is_already_logged(self):
        session = [
            item for item in self.session_items() if item.target() == "2026-01-02T08:05"
        ][0]
        first = self.option_items(session)[1]
        self.plugin.on_execute(first, None)

        again = self.option_items(session)[1]
        self.assertIn("bereits erfasst", again.short_desc())

    def test_broken_data_bag_shows_error(self):
        broken = _Item(WorkLog.ITEMCAT_SESSION, "Mi 09:04", "", "x", data_bag="{}")
        self.plugin.on_suggest("", [self.keyword_item(), broken])
        self.assertEqual(
            "Session no longer available", self.plugin.suggestions[0].label()
        )


class TestJournalWriting(_PluginTestCase):
    def _first_option(self, target="2026-01-02T08:05", index=1):
        session = [item for item in self.session_items() if item.target() == target][0]
        return self.option_items(session)[index]

    def test_default_action_writes_the_entry(self):
        self.plugin.on_execute(self._first_option(), None)

        content = self.read_journal()
        self.assertIn("@arbeitsstunden am 2026-01-02: 8,5h", content)
        self.assertTrue(content.startswith("# Fr 2026-01-02 "))

    def test_write_action_writes_the_entry(self):
        action = _Action(WorkLog.ACTION_WRITE)
        self.plugin.on_execute(self._first_option(), action)
        self.assertIn("@arbeitsstunden am 2026-01-02", self.read_journal())

    def test_copy_action_does_not_touch_the_file(self):
        action = _Action(WorkLog.ACTION_COPY)
        self.plugin.on_execute(self._first_option(), action)

        self.assertFalse(os.path.exists(self.journal))
        self.assertEqual(1, len(kpu_stub.clipboard))
        self.assertIn("@arbeitsstunden am 2026-01-02", kpu_stub.clipboard[0])

    def test_second_entry_is_appended(self):
        self.plugin.on_execute(self._first_option(), None)
        self.plugin.on_execute(self._first_option(target="2025-11-28T08:44"), None)

        content = self.read_journal()
        self.assertIn("@arbeitsstunden am 2026-01-02", content)
        self.assertIn("@arbeitsstunden am 2025-11-28", content)

    def test_custom_templates_are_used(self):
        self.plugin.settings.values.update(
            {
                "journal_header": "## {weekday} {date}",
                "journal_entry": "worked {hours}",
            }
        )
        self.plugin.on_events(1)
        self.plugin.on_execute(self._first_option(), None)

        self.assertEqual("## Fr 2026-01-02\nworked 8,5h\n", self.read_journal())

    def test_unwritable_journal_is_reported(self):
        blocker = os.path.join(self.folder, "blocker")
        with open(blocker, "w", encoding="utf-8") as handle:
            handle.write("not a folder")
        self.plugin.settings.values["journal_file"] = os.path.join(
            blocker, "Journal.log"
        )
        self.plugin.on_events(1)
        self.plugin.on_execute(self._first_option(), None)

        self.assertTrue(any(level == "err" for level, _ in self.plugin.messages))

    def test_enter_on_a_session_copies_the_summary(self):
        session = self.session_items()[0]
        self.plugin.on_execute(session, None)
        self.assertEqual(1, len(kpu_stub.clipboard))


class TestShortcuts(_PluginTestCase):
    def test_hash_lists_all_shortcuts(self):
        self.plugin.on_suggest("#", [self.keyword_item()])
        self.assertEqual(
            ["#edit", "#journal", "#source"],
            [item.label() for item in self.plugin.suggestions],
        )

    def test_prefix_filters_shortcuts(self):
        self.plugin.on_suggest("#jou", [self.keyword_item()])
        self.assertEqual(
            ["#journal"], [item.label() for item in self.plugin.suggestions]
        )

    def test_unknown_shortcut(self):
        self.plugin.on_suggest("#nope", [self.keyword_item()])
        self.assertIn("Unknown shortcut", self.plugin.suggestions[0].short_desc())

    def test_source_shortcut_opens_the_event_log(self):
        item = _Item(WorkLog.ITEMCAT_SHORTCUT, "#source", "", "open_source")
        self.plugin.on_execute(item, None)
        self.assertEqual([FIXTURE], kpu_stub.executed)

    def test_journal_shortcut_warns_when_missing(self):
        item = _Item(WorkLog.ITEMCAT_SHORTCUT, "#journal", "", "open_journal")
        self.plugin.on_execute(item, None)
        self.assertEqual([], kpu_stub.executed)
        self.assertTrue(any(level == "warn" for level, _ in self.plugin.messages))

    def test_edit_shortcut_opens_the_ini(self):
        item = _Item(WorkLog.ITEMCAT_SHORTCUT, "#edit", "", "edit_config")
        self.plugin.on_execute(item, None)
        self.assertEqual(1, len(kpu_stub.executed))
        self.assertTrue(kpu_stub.executed[0].endswith("keypi_worklog.ini"))


class TestUserStoryWorkflow(_PluginTestCase):
    """The exact example from the user story"""

    def setUp(self):
        super().setUp()
        self.log = os.path.join(self.folder, "winevent.log")
        with open(self.log, "w", encoding="utf-8") as handle:
            handle.write(
                "   35735 Aug 19 09:04  Information EventLog"
                "               2147489653 Der Ereignisprotokolldienst wurde gestartet.\n"
            )
        self.plugin.settings.values["winevent_log"] = self.log
        self.plugin.on_events(1)

    def test_start_time_is_listed(self):
        items = self.session_items()
        self.assertEqual(1, len(items))
        self.assertTrue(items[0].label().endswith("09:04"))

    def test_options_and_journal_entry(self):
        """Called at 17:09 the day shows 8h / 7h / 6,5h"""
        session = self.session_items()[0]

        # Freeze "now" at 17:09 by rebuilding the session from a fixed data bag
        session._data_bag = '{"start": "%s", "end": "%s", "running": false}' % (
            datetime(date.today().year, 8, 19, 9, 4).isoformat(timespec="minutes"),
            datetime(date.today().year, 8, 19, 17, 9).isoformat(timespec="minutes"),
        )
        options = self.option_items(session)

        self.assertEqual(
            ["8h · ohne Pause", "7h · 1h Pause", "6,5h · 1,5h Pause"],
            [item.label() for item in options],
        )

        self.plugin.on_execute(options[1], None)
        year = date.today().year
        self.assertIn(f"@arbeitsstunden am {year}-08-19: 7h", self.read_journal())


if __name__ == "__main__":
    unittest.main()
