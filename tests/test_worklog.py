"""
Unit tests for the WorkLog plugin domain logic.

The module under test is loaded directly from its file, because importing
keypi_worklog as a package would pull in keypirinha, which only exists inside
the launcher.
"""

import importlib.util
import os
import tempfile
import unittest
from datetime import date, datetime

_MODULE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "keypi_worklog",
    "lib",
    "worklog.py",
)
_SPEC = importlib.util.spec_from_file_location("worklog", _MODULE_PATH)
worklog = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(worklog)

FIXTURE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "winevent_sample.log"
)

START_LINE = (
    "   35735 {month} {day:02d} {time}  Information EventLog"
    "               2147489653 Der Ereignisprotokolldienst wurde gestartet."
)
STOP_LINE = (
    "   35724 {month} {day:02d} {time}  Information EventLog"
    "               2147489654 Der Ereignisprotokolldienst wurde beendet."
)


def start(month, day, time):
    return START_LINE.format(month=month, day=day, time=time)


def stop(month, day, time):
    return STOP_LINE.format(month=month, day=day, time=time)


class TestParseEvents(unittest.TestCase):
    """Parsing of the Windows event log export"""

    def test_parses_start_and_stop(self):
        text = "\n".join([stop("Aug", 18, "17:28"), start("Aug", 18, "08:10")])
        events = worklog.parse_events(text, today=date(2026, 8, 19))

        self.assertEqual(2, len(events))
        self.assertEqual("stop", events[0].kind)
        self.assertEqual(datetime(2026, 8, 18, 17, 28), events[0].when)
        self.assertEqual("start", events[1].kind)
        self.assertEqual(datetime(2026, 8, 18, 8, 10), events[1].when)

    def test_ignores_empty_and_malformed_lines(self):
        text = "\n".join(
            [
                "",
                "   ---- corrupted record ----",
                "no timestamp here at all",
                start("Aug", 19, "09:04"),
            ]
        )
        events = worklog.parse_events(text, today=date(2026, 8, 19))
        self.assertEqual(1, len(events))

    def test_ignores_unknown_month(self):
        text = start("Xyz", 19, "09:04")
        self.assertEqual([], worklog.parse_events(text, today=date(2026, 8, 19)))

    def test_ignores_other_event_sources(self):
        """Other providers use the same wording and must not count as work time"""
        text = (
            "    9118 Jan 05 08:11  Information Service Control"
            "        1073748860 Ein Dienst wurde erfolgreich gestartet."
        )
        self.assertEqual([], worklog.parse_events(text, today=date(2026, 1, 5)))

    def test_ignores_impossible_times(self):
        text = start("Aug", 19, "29:04")
        self.assertEqual([], worklog.parse_events(text, today=date(2026, 8, 19)))

    def test_accepts_german_and_english_month_names(self):
        for month in ("Mai", "May", "Mrz", "Mar", "Okt", "Oct", "Dez", "Dec"):
            with self.subTest(month=month):
                events = worklog.parse_events(
                    start(month, 5, "08:00"), today=date(2026, 12, 31)
                )
                self.assertEqual(1, len(events), month)

    def test_handles_crlf_line_endings(self):
        text = start("Aug", 19, "09:04") + "\r\n" + stop("Aug", 18, "17:28") + "\r\n"
        self.assertEqual(2, len(worklog.parse_events(text, today=date(2026, 8, 19))))

    def test_empty_input(self):
        self.assertEqual([], worklog.parse_events("", today=date(2026, 8, 19)))

    def test_custom_markers(self):
        text = "   1 Aug 19 09:04  Information EventLog  1 The service was launched."
        events = worklog.parse_events(
            text,
            today=date(2026, 8, 19),
            start_marker="launched",
            stop_marker="halted",
        )
        self.assertEqual(1, len(events))
        self.assertEqual("start", events[0].kind)


class TestYearInference(unittest.TestCase):
    """The export has no year, it has to be derived from the sort order"""

    def test_same_year_when_descending(self):
        text = "\n".join([start("Aug", 19, "09:04"), start("Aug", 18, "08:10")])
        events = worklog.parse_events(text, today=date(2026, 8, 19))
        self.assertEqual(2026, events[0].when.year)
        self.assertEqual(2026, events[1].when.year)

    def test_year_rollover_january_to_december(self):
        text = "\n".join([start("Jan", 2, "08:05"), start("Dez", 31, "07:58")])
        events = worklog.parse_events(text, today=date(2026, 1, 5))
        self.assertEqual(datetime(2026, 1, 2, 8, 5), events[0].when)
        self.assertEqual(datetime(2025, 12, 31, 7, 58), events[1].when)

    def test_multiple_rollovers(self):
        text = "\n".join(
            [
                start("Jan", 5, "08:00"),
                start("Dez", 1, "08:00"),
                start("Jan", 3, "08:00"),
            ]
        )
        events = worklog.parse_events(text, today=date(2026, 1, 5))
        self.assertEqual([2026, 2025, 2025], [event.when.year for event in events])

    def test_entry_newer_than_today_belongs_to_previous_year(self):
        text = start("Dez", 30, "08:00")
        events = worklog.parse_events(text, today=date(2026, 1, 5))
        self.assertEqual(2025, events[0].when.year)

    def test_february_29th_falls_back_to_a_leap_year(self):
        text = start("Feb", 29, "08:00")
        events = worklog.parse_events(text, today=date(2026, 3, 1))
        self.assertEqual(datetime(2024, 2, 29, 8, 0), events[0].when)


class TestBuildSessions(unittest.TestCase):
    """Pairing of start and stop events"""

    def _events(self, *lines):
        return worklog.parse_events("\n".join(lines), today=date(2026, 8, 19))

    def test_pairs_start_with_following_stop(self):
        events = self._events(stop("Aug", 18, "17:28"), start("Aug", 18, "08:10"))
        sessions = worklog.build_sessions(events, now=datetime(2026, 8, 19, 17, 9))

        self.assertEqual(1, len(sessions))
        self.assertEqual(datetime(2026, 8, 18, 8, 10), sessions[0].start)
        self.assertEqual(datetime(2026, 8, 18, 17, 28), sessions[0].end)
        self.assertFalse(sessions[0].running)

    def test_running_session_ends_now(self):
        events = self._events(start("Aug", 19, "09:04"))
        now = datetime(2026, 8, 19, 17, 9)
        sessions = worklog.build_sessions(events, now=now)

        self.assertTrue(sessions[0].running)
        self.assertEqual(now, sessions[0].end)

    def test_two_sessions_on_the_same_day(self):
        """Both starts of a past day end at the last stop of that day"""
        events = self._events(
            stop("Aug", 12, "21:51"),
            start("Aug", 12, "19:34"),
            stop("Aug", 12, "17:13"),
            start("Aug", 12, "09:06"),
        )
        sessions = worklog.build_sessions(events, now=datetime(2026, 8, 19, 17, 9))

        self.assertEqual(2, len(sessions))
        self.assertEqual(datetime(2026, 8, 12, 19, 34), sessions[0].start)
        self.assertEqual(datetime(2026, 8, 12, 21, 51), sessions[0].end)
        self.assertEqual(datetime(2026, 8, 12, 9, 6), sessions[1].start)
        self.assertEqual(datetime(2026, 8, 12, 21, 51), sessions[1].end)

    def test_reboot_today_does_not_cut_the_working_time(self):
        """A reboot must not end the entry that started the working day"""
        events = self._events(
            start("Aug", 19, "09:57"),
            stop("Aug", 19, "09:57"),
            start("Aug", 19, "09:02"),
        )
        sessions = worklog.build_sessions(events, now=datetime(2026, 8, 19, 16, 39))

        self.assertEqual(2, len(sessions))
        self.assertEqual(datetime(2026, 8, 19, 16, 39), sessions[0].end)
        self.assertEqual(datetime(2026, 8, 19, 9, 2), sessions[1].start)
        self.assertEqual(datetime(2026, 8, 19, 16, 39), sessions[1].end)
        self.assertEqual(457, worklog.session_minutes(sessions[1]))

    def test_every_start_of_today_ends_now(self):
        events = self._events(
            start("Aug", 19, "13:00"),
            start("Aug", 19, "11:00"),
            start("Aug", 19, "09:00"),
        )
        now = datetime(2026, 8, 19, 17, 0)
        sessions = worklog.build_sessions(events, now=now)

        self.assertEqual([now, now, now], [session.end for session in sessions])
        self.assertTrue(all(session.running for session in sessions))

    def test_reboot_on_a_past_day_uses_the_last_stop_of_that_day(self):
        events = self._events(
            stop("Aug", 18, "17:38"),
            start("Aug", 18, "12:10"),
            stop("Aug", 18, "12:09"),
            start("Aug", 18, "08:25"),
        )
        sessions = worklog.build_sessions(events, now=datetime(2026, 8, 19, 17, 9))

        self.assertEqual(datetime(2026, 8, 18, 17, 38), sessions[0].end)
        self.assertEqual(datetime(2026, 8, 18, 8, 25), sessions[1].start)
        self.assertEqual(datetime(2026, 8, 18, 17, 38), sessions[1].end)
        self.assertEqual(553, worklog.session_minutes(sessions[1]))

    def test_stop_before_the_start_is_not_used(self):
        """The logoff of the previous day must not end the next start"""
        events = self._events(
            start("Aug", 18, "17:00"),
            stop("Aug", 18, "08:00"),
        )
        sessions = worklog.build_sessions(events, now=datetime(2026, 8, 19, 17, 9))

        self.assertIsNone(sessions[0].end)

    def test_session_across_midnight(self):
        events = self._events(stop("Aug", 5, "01:06"), start("Aug", 4, "23:43"))
        sessions = worklog.build_sessions(events, now=datetime(2026, 8, 19, 17, 9))

        self.assertEqual(83, worklog.session_minutes(sessions[0]))

    def test_start_without_stop_has_no_end(self):
        """A crash leaves a start event that is superseded by the next start"""
        events = self._events(start("Aug", 19, "09:04"), start("Aug", 18, "08:10"))
        sessions = worklog.build_sessions(events, now=datetime(2026, 8, 19, 17, 9))

        self.assertEqual(2, len(sessions))
        self.assertTrue(sessions[0].running)
        self.assertIsNone(sessions[1].end)
        self.assertIsNone(worklog.session_minutes(sessions[1]))

    def test_max_entries_limits_the_result(self):
        lines = []
        for day in range(19, 9, -1):
            lines.append(stop("Aug", day, "17:00"))
            lines.append(start("Aug", day, "08:00"))
        sessions = worklog.build_sessions(
            self._events(*lines), now=datetime(2026, 8, 19, 17, 9), max_entries=3
        )
        self.assertEqual(3, len(sessions))

    def test_no_events_yields_no_sessions(self):
        self.assertEqual(
            [], worklog.build_sessions([], now=datetime(2026, 8, 19, 17, 9))
        )


class TestFixtureFile(unittest.TestCase):
    """End to end test against the sample log"""

    def setUp(self):
        self.now = datetime(2026, 1, 5, 17, 9, 44)
        self.sessions = worklog.load_sessions(FIXTURE, now=self.now, max_entries=None)

    def test_session_count(self):
        self.assertEqual(9, len(self.sessions))

    def test_newest_session_is_running(self):
        self.assertTrue(self.sessions[0].running)
        self.assertEqual(datetime(2026, 1, 5, 8, 12), self.sessions[0].start)
        self.assertEqual(self.now, self.sessions[0].end)

    def test_year_rollover_in_fixture(self):
        self.assertEqual(datetime(2025, 12, 31, 7, 58), self.sessions[2].start)

    def test_midnight_crossing_in_fixture(self):
        session = self.sessions[3]
        self.assertEqual(datetime(2025, 12, 29, 23, 43), session.start)
        self.assertEqual(datetime(2025, 12, 30, 1, 6), session.end)

    def test_sessions_are_sorted_newest_first(self):
        starts = [session.start for session in self.sessions]
        self.assertEqual(starts, sorted(starts, reverse=True))


class TestRounding(unittest.TestCase):
    """Rounding is applied to the difference, not to start and end"""

    def test_user_story_example(self):
        """09:04 to 17:09 is 8h05m and has to round down to 8h"""
        minutes = worklog.minutes_between(
            datetime(2026, 8, 19, 9, 4), datetime(2026, 8, 19, 17, 9)
        )
        self.assertEqual(485, minutes)
        self.assertEqual(480, worklog.round_minutes(minutes))

    def test_rounds_up_from_half_step(self):
        self.assertEqual(495, worklog.round_minutes(488))
        # 487.5 is the half point, 487 still rounds down
        self.assertEqual(480, worklog.round_minutes(487))

    def test_rounds_down_below_half_step(self):
        self.assertEqual(480, worklog.round_minutes(486))

    def test_exact_quarter_stays(self):
        self.assertEqual(480, worklog.round_minutes(480))

    def test_zero_and_negative(self):
        self.assertEqual(0, worklog.round_minutes(0))
        self.assertEqual(0, worklog.round_minutes(-30))

    def test_custom_step(self):
        self.assertEqual(480, worklog.round_minutes(485, 30))
        self.assertEqual(510, worklog.round_minutes(496, 30))
        self.assertEqual(485, worklog.round_minutes(485, 1))


class TestFormatting(unittest.TestCase):
    """German number formatting for the journal"""

    def test_format_hours(self):
        self.assertEqual("8h", worklog.format_hours(480))
        self.assertEqual("7h", worklog.format_hours(420))
        self.assertEqual("6,5h", worklog.format_hours(390))
        self.assertEqual("7,25h", worklog.format_hours(435))
        self.assertEqual("0,25h", worklog.format_hours(15))
        self.assertEqual("0h", worklog.format_hours(0))

    def test_format_duration(self):
        self.assertEqual("8h 05m", worklog.format_duration(485))
        self.assertEqual("0h 00m", worklog.format_duration(0))
        self.assertEqual("12h 45m", worklog.format_duration(765))

    def test_weekday_abbreviations(self):
        self.assertEqual("Mi", worklog.weekday_abbr(date(2026, 8, 19)))
        self.assertEqual("So", worklog.weekday_abbr(date(2026, 8, 16)))

    def test_iso_week(self):
        self.assertEqual(34, worklog.iso_week(date(2026, 8, 19)))


class TestBreakOptions(unittest.TestCase):
    """Break variants offered after selecting a session"""

    def test_default_options_match_the_user_story(self):
        options = worklog.build_break_options(480)
        self.assertEqual(
            [("8h", "ohne Pause"), ("7h", "1h Pause"), ("6,5h", "1,5h Pause")],
            [(option["hours"], option["break_label"]) for option in options],
        )

    def test_breaks_longer_than_the_working_time_are_dropped(self):
        options = worklog.build_break_options(30)
        self.assertEqual(1, len(options))
        self.assertEqual(0, options[0]["break_minutes"])

    def test_break_equal_to_the_working_time_is_dropped(self):
        options = worklog.build_break_options(60)
        self.assertEqual(
            [("1h", "ohne Pause")],
            [(option["hours"], option["break_label"]) for option in options],
        )

    def test_no_options_without_working_time(self):
        self.assertEqual([], worklog.build_break_options(0))

    def test_custom_breaks(self):
        options = worklog.build_break_options(480, [30, 45])
        self.assertEqual(
            [("7,5h", "0,5h Pause"), ("7,25h", "0,75h Pause")],
            [(option["hours"], option["break_label"]) for option in options],
        )

    def test_parse_break_options(self):
        self.assertEqual([0, 60, 90], worklog.parse_break_options("0, 60, 90"))
        self.assertEqual([0, 60], worklog.parse_break_options(" 0 ;60 "))
        self.assertEqual([30], worklog.parse_break_options("30"))

    def test_parse_break_options_drops_invalid_values(self):
        self.assertEqual([0, 60], worklog.parse_break_options("0, abc, 60, -15"))

    def test_parse_break_options_keeps_order_and_removes_duplicates(self):
        self.assertEqual([90, 0], worklog.parse_break_options("90, 0, 90"))

    def test_parse_break_options_falls_back(self):
        self.assertEqual([0, 60, 90], worklog.parse_break_options(""))
        self.assertEqual([0, 60, 90], worklog.parse_break_options(None))
        self.assertEqual([0, 60, 90], worklog.parse_break_options("abc"))


class TestIntSetting(unittest.TestCase):
    """INI values must never crash the plugin"""

    def test_valid_value(self):
        self.assertEqual(15, worklog.parse_int_setting("15", 30))

    def test_invalid_value_falls_back(self):
        self.assertEqual(30, worklog.parse_int_setting("abc", 30))
        self.assertEqual(30, worklog.parse_int_setting(None, 30))
        self.assertEqual(30, worklog.parse_int_setting("", 30))

    def test_out_of_range_falls_back(self):
        self.assertEqual(15, worklog.parse_int_setting("0", 15, minimum=1))
        self.assertEqual(15, worklog.parse_int_setting("999", 15, maximum=60))


class TestJournalRendering(unittest.TestCase):
    """The journal block has to match the format from the user story"""

    def test_default_format(self):
        text = worklog.render_journal_entry(
            date(2026, 8, 19), datetime(2026, 8, 19, 17, 9, 44), "7h"
        )
        self.assertEqual(
            "# Mi 2026-08-19 1709:44\n@arbeitsstunden am 2026-08-19: 7h\n", text
        )

    def test_custom_templates(self):
        text = worklog.render_journal_entry(
            date(2026, 8, 19),
            datetime(2026, 8, 19, 17, 9, 44),
            "7h",
            header_template="## {weekday} KW{week}",
            entry_template="worked {hours} on {date} ({clock})",
        )
        self.assertEqual("## Mi KW34\nworked 7h on 2026-08-19 (17:09)\n", text)

    def test_broken_template_falls_back_to_default(self):
        text = worklog.render_journal_entry(
            date(2026, 8, 19),
            datetime(2026, 8, 19, 17, 9, 44),
            "7h",
            header_template="# {does_not_exist}",
        )
        self.assertTrue(text.startswith("# Mi 2026-08-19 1709:44"))


class TestJournalFile(unittest.TestCase):
    """Writing to the journal file"""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.path = os.path.join(self.folder, "Journal.log")
        self.block = worklog.render_journal_entry(
            date(2026, 8, 19), datetime(2026, 8, 19, 17, 9, 44), "7h"
        )

    def _read(self):
        with open(self.path, encoding="utf-8") as handle:
            return handle.read()

    def test_creates_missing_file(self):
        worklog.append_journal_entry(self.path, self.block)
        self.assertEqual(self.block, self._read())

    def test_creates_missing_folder(self):
        path = os.path.join(self.folder, "logs", "sub", "Journal.log")
        worklog.append_journal_entry(path, self.block)
        self.assertTrue(os.path.isfile(path))

    def test_appends_blank_line_between_blocks(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("# old entry\n")

        worklog.append_journal_entry(self.path, self.block)
        self.assertEqual("# old entry\n\n" + self.block, self._read())

    def test_appends_newline_when_file_has_no_trailing_newline(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("# old entry")

        worklog.append_journal_entry(self.path, self.block)
        self.assertEqual("# old entry\n\n" + self.block, self._read())

    def test_does_not_add_more_than_one_blank_line(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("# old entry\n\n")

        worklog.append_journal_entry(self.path, self.block)
        self.assertEqual("# old entry\n\n" + self.block, self._read())

    def test_duplicate_detection(self):
        self.assertFalse(worklog.journal_contains_date(self.path, date(2026, 8, 19)))

        worklog.append_journal_entry(self.path, self.block)

        self.assertTrue(worklog.journal_contains_date(self.path, date(2026, 8, 19)))
        self.assertFalse(worklog.journal_contains_date(self.path, date(2026, 8, 18)))

    def test_duplicate_detection_without_file(self):
        missing = os.path.join(self.folder, "nope.log")
        self.assertFalse(worklog.journal_contains_date(missing, date(2026, 8, 19)))

    def test_find_journal_hours(self):
        worklog.append_journal_entry(self.path, self.block)
        self.assertEqual("7h", worklog.find_journal_hours(self.path, date(2026, 8, 19)))
        self.assertIsNone(worklog.find_journal_hours(self.path, date(2026, 8, 18)))

    def test_find_journal_hours_returns_latest_entry(self):
        worklog.append_journal_entry(self.path, self.block)
        worklog.append_journal_entry(
            self.path,
            worklog.render_journal_entry(
                date(2026, 8, 19), datetime(2026, 8, 19, 18, 0, 0), "8h"
            ),
        )
        self.assertEqual("8h", worklog.find_journal_hours(self.path, date(2026, 8, 19)))

    def test_reads_files_written_in_cp1252(self):
        with open(self.path, "wb") as handle:
            handle.write("# Mrz\n@arbeitsstunden am 2026-08-19: 7h\n".encode("cp1252"))
        self.assertTrue(worklog.journal_contains_date(self.path, date(2026, 8, 19)))


class TestSessionDescription(unittest.TestCase):
    """Texts shown in the launcher"""

    def test_running_session(self):
        session = worklog.Session(
            start=datetime(2026, 8, 19, 9, 4),
            end=datetime(2026, 8, 19, 17, 9),
            running=True,
        )
        described = worklog.describe_session(session)

        self.assertEqual("Mi 09:04", described["label"])
        self.assertIn("bis jetzt 17:09", described["description"])
        self.assertIn("KW 34", described["description"])
        self.assertEqual(485, described["raw_minutes"])
        self.assertEqual(480, described["rounded_minutes"])

    def test_closed_session(self):
        session = worklog.Session(
            start=datetime(2026, 8, 18, 8, 10),
            end=datetime(2026, 8, 18, 17, 28),
            running=False,
        )
        described = worklog.describe_session(session)

        self.assertEqual("Di 08:10", described["label"])
        self.assertIn("bis 17:28", described["description"])

    def test_session_without_end(self):
        session = worklog.Session(
            start=datetime(2026, 8, 18, 8, 10), end=None, running=False
        )
        described = worklog.describe_session(session)

        self.assertIsNone(described["rounded_minutes"])
        self.assertIn("kein Abmelde-Event", described["description"])


class TestSessionKey(unittest.TestCase):
    """Item targets encode the session so no state has to be kept"""

    def test_roundtrip(self):
        session = worklog.Session(
            start=datetime(2026, 8, 19, 9, 4), end=None, running=False
        )
        key = worklog.session_key(session)

        self.assertEqual("2026-08-19T09:04", key)
        self.assertEqual(datetime(2026, 8, 19, 9, 4), worklog.parse_session_key(key))

    def test_invalid_key(self):
        self.assertIsNone(worklog.parse_session_key("nonsense"))
        self.assertIsNone(worklog.parse_session_key(None))

    def test_keys_are_unique_per_session(self):
        sessions = worklog.load_sessions(
            FIXTURE, now=datetime(2026, 1, 5, 17, 9), max_entries=None
        )
        keys = [worklog.session_key(session) for session in sessions]
        self.assertEqual(len(keys), len(set(keys)))


class TestReadTextFile(unittest.TestCase):
    """Encoding tolerance for the log export"""

    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def _write(self, data):
        path = os.path.join(self.folder, "log.txt")
        with open(path, "wb") as handle:
            handle.write(data)
        return path

    def test_utf8(self):
        path = self._write("Mär\n".encode("utf-8"))
        self.assertEqual("Mär\n", worklog.read_text_file(path))

    def test_utf8_with_bom(self):
        path = self._write("Mär\n".encode("utf-8-sig"))
        self.assertEqual("Mär\n", worklog.read_text_file(path))

    def test_cp1252(self):
        path = self._write("Mär\n".encode("cp1252"))
        self.assertEqual("Mär\n", worklog.read_text_file(path))

    def test_utf16(self):
        path = self._write("Mär\n".encode("utf-16"))
        self.assertEqual("Mär\n", worklog.read_text_file(path))

    def test_missing_file_raises(self):
        with self.assertRaises(OSError):
            worklog.read_text_file(os.path.join(self.folder, "missing.txt"))


if __name__ == "__main__":
    unittest.main()
