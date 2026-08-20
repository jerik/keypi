"""
Work log logic for the Keypirinha WorkLog plugin.

This module contains the whole domain logic: reading the Windows event log
export, turning it into work sessions, rounding durations and writing journal
entries. It deliberately does NOT import keypirinha, so it can be unit tested
with plain pytest.
"""

import math
import os
import re
from collections import namedtuple
from datetime import date, datetime, timedelta

# Defaults, also used as fallbacks when the INI contains invalid values
DEFAULT_SOURCE = "EventLog"
DEFAULT_START_MARKER = "gestartet"
DEFAULT_STOP_MARKER = "beendet"
DEFAULT_BREAK_OPTIONS = (0, 60, 90)
DEFAULT_ROUNDING_MINUTES = 15
DEFAULT_MAX_ENTRIES = 30
DEFAULT_JOURNAL_HEADER = "# {weekday} {date} {time}"
DEFAULT_JOURNAL_ENTRY = "@arbeitsstunden am {date}: {hours}"

# German weekday abbreviations, indexed by date.weekday()
WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")

# Month abbreviations as written by German and English Windows installations.
# Using a lookup table avoids locale.setlocale(), which is process global and
# would affect every other Keypirinha plugin.
MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "mrz": 3,
    "mär": 3,
    "maer": 3,
    "apr": 4,
    "may": 5,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "okt": 10,
    "oct": 10,
    "nov": 11,
    "dec": 12,
    "dez": 12,
}

# "   35735 Aug 19 09:04  Information EventLog  2147489653 Der ... gestartet."
# The leading record number is optional, column widths are not relied upon.
_EVENT_LINE = re.compile(
    r"^\s*(?:\d+\s+)?([A-Za-zÄÖÜäöüß]{3,4})\s+(\d{1,2})\s+(\d{1,2}):(\d{2})\s+(.+)$"
)

#: A single log event. ``kind`` is either "start" or "stop".
LogEvent = namedtuple("LogEvent", "kind when")

#: A work session. ``end`` is None when no matching stop event exists.
#: ``running`` marks a session that has not been closed yet, where ``end``
#: is the current time instead of a logged stop event.
Session = namedtuple("Session", "start end running")


# ---------------------------------------------------------------------------
# File access
# ---------------------------------------------------------------------------


def read_text_file(path):
    """
    Read a text file, tolerating the encodings Windows exports typically use.

    Args:
        path: Path to the file

    Returns:
        The file content as str

    Raises:
        OSError: If the file cannot be read
    """
    with open(path, "rb") as handle:
        raw = handle.read()

    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")

    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _resolve_date(year, month, day):
    """
    Build a date, stepping back through years until the day exists.

    Needed for February 29th, which is only valid in leap years.
    """
    for _ in range(5):
        try:
            return date(year, month, day)
        except ValueError:
            year -= 1
    return None


def parse_events(
    text,
    today=None,
    source=DEFAULT_SOURCE,
    start_marker=DEFAULT_START_MARKER,
    stop_marker=DEFAULT_STOP_MARKER,
):
    """
    Parse a Windows event log export into start/stop events.

    The export has no year, so the year is derived from ``today``: the log is
    sorted newest first, therefore the year is decremented whenever the
    month/day of an entry is later than the entry before it.

    Args:
        text: Content of the log file
        today: Reference date for the year, defaults to date.today()
        source: Event source that identifies the relevant lines
        start_marker: Substring marking a logon/boot event
        stop_marker: Substring marking a logoff/shutdown event

    Returns:
        List of LogEvent, newest first
    """
    if today is None:
        today = date.today()

    source_key = source.lower()
    start_key = start_marker.lower()
    stop_key = stop_marker.lower()

    year = today.year
    previous = (today.month, today.day)
    events = []

    for line in text.splitlines():
        match = _EVENT_LINE.match(line)
        if not match:
            continue

        month_name, day_text, hour_text, minute_text, rest = match.groups()
        month = MONTHS.get(month_name.lower())
        if month is None:
            continue

        rest_key = rest.lower()
        if source_key and source_key not in rest_key:
            # Other providers may use the same wording ("Ein Dienst wurde
            # erfolgreich gestartet") and must not be counted as work time.
            continue

        if start_key and start_key in rest_key:
            kind = "start"
        elif stop_key and stop_key in rest_key:
            kind = "stop"
        else:
            continue

        day = int(day_text)
        hour = int(hour_text)
        minute = int(minute_text)
        if hour > 23 or minute > 59:
            continue

        if (month, day) > previous:
            year -= 1
        previous = (month, day)

        day_date = _resolve_date(year, month, day)
        if day_date is None:
            continue

        events.append(
            LogEvent(
                kind=kind,
                when=datetime(
                    day_date.year, day_date.month, day_date.day, hour, minute
                ),
            )
        )

    return events


def build_sessions(events, now=None, max_entries=DEFAULT_MAX_ENTRIES):
    """
    Turn log events into work sessions, newest first.

    Every start event is paired with the next stop event that follows it in
    time. A start event without such a stop event is a running session and
    ends at ``now``. If another start event appears first, the session was
    never closed properly and gets end=None.

    Args:
        events: List of LogEvent, newest first
        now: Current time, defaults to datetime.now()
        max_entries: Maximum number of sessions to return, None for all

    Returns:
        List of Session, newest first
    """
    if now is None:
        now = datetime.now()

    sessions = []

    for index, event in enumerate(events):
        if event.kind != "start":
            continue

        end = None
        running = False
        for candidate in reversed(events[:index]):
            if candidate.kind == "start":
                # Session was superseded by a later start without a stop event
                break
            if candidate.when >= event.when:
                end = candidate.when
                break
        else:
            # Nothing newer in the log: the session is still running
            end = now
            running = True

        sessions.append(Session(start=event.when, end=end, running=running))

        if max_entries is not None and len(sessions) >= max_entries:
            break

    return sessions


def load_sessions(
    path,
    now=None,
    max_entries=DEFAULT_MAX_ENTRIES,
    source=DEFAULT_SOURCE,
    start_marker=DEFAULT_START_MARKER,
    stop_marker=DEFAULT_STOP_MARKER,
):
    """
    Read the event log and return the most recent work sessions.

    Args:
        path: Path to the event log export
        now: Current time, defaults to datetime.now()
        max_entries: Maximum number of sessions to return

    Returns:
        List of Session, newest first

    Raises:
        OSError: If the file cannot be read
    """
    if now is None:
        now = datetime.now()

    text = read_text_file(path)
    events = parse_events(
        text,
        today=now.date(),
        source=source,
        start_marker=start_marker,
        stop_marker=stop_marker,
    )
    return build_sessions(events, now=now, max_entries=max_entries)


# ---------------------------------------------------------------------------
# Durations
# ---------------------------------------------------------------------------


def session_minutes(session):
    """
    Raw duration of a session in minutes, or None if it has no end.
    """
    if session.end is None:
        return None
    minutes = int((session.end - session.start).total_seconds() // 60)
    return max(minutes, 0)


def round_minutes(minutes, step=DEFAULT_ROUNDING_MINUTES):
    """
    Round minutes to the nearest step, halves rounded up.

    The rounding is applied to the difference, not to start and end
    separately: 8h05m -> 8h00m, 8h08m -> 8h15m.
    """
    if step <= 1:
        return max(int(minutes), 0)
    rounded = int(math.floor(minutes / step + 0.5)) * step
    return max(rounded, 0)


def format_hours(minutes):
    """
    Format minutes as German decimal hours: 480 -> "8h", 390 -> "6,5h".
    """
    text = "{:.2f}".format(minutes / 60).rstrip("0").rstrip(".")
    if not text or text == "-0":
        text = "0"
    return text.replace(".", ",") + "h"


def format_duration(minutes):
    """
    Format minutes as clock duration: 485 -> "8h 05m".
    """
    minutes = max(int(minutes), 0)
    return "{}h {:02d}m".format(minutes // 60, minutes % 60)


def parse_break_options(text, fallback=DEFAULT_BREAK_OPTIONS):
    """
    Parse the break_options setting ("0, 60, 90") into a list of minutes.

    Invalid and duplicate entries are dropped, the configured order is kept.
    An empty or completely invalid setting falls back to the default.
    """
    values = []
    for part in str(text or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            minutes = int(part)
        except ValueError:
            continue
        if minutes < 0 or minutes in values:
            continue
        values.append(minutes)

    return values or list(fallback)


def build_break_options(worked_minutes, breaks=DEFAULT_BREAK_OPTIONS):
    """
    Build the selectable break variants for a work duration.

    Args:
        worked_minutes: Rounded working time in minutes
        breaks: Break lengths in minutes

    Returns:
        List of dicts with break_minutes, net_minutes, hours and break_label.
        Variants that leave no working time are dropped.
    """
    options = []
    for break_minutes in breaks:
        net = worked_minutes - break_minutes
        if net <= 0:
            # Nothing left to log after the break
            continue
        if break_minutes == 0:
            label = "ohne Pause"
        else:
            label = "{} Pause".format(format_hours(break_minutes))
        options.append(
            {
                "break_minutes": break_minutes,
                "net_minutes": net,
                "hours": format_hours(net),
                "break_label": label,
            }
        )
    return options


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def weekday_abbr(day):
    """German weekday abbreviation for a date or datetime."""
    return WEEKDAYS[day.weekday()]


def iso_week(day):
    """ISO calendar week number for a date or datetime."""
    return day.isocalendar()[1]


def _format_template(template, fallback, values):
    """Format a user supplied template, falling back on bad placeholders."""
    try:
        return template.format(**values)
    except (KeyError, IndexError, ValueError):
        return fallback.format(**values)


def journal_values(day, timestamp, hours_text):
    """Placeholder values available in the journal templates."""
    return {
        "weekday": weekday_abbr(day),
        "date": day.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H%M:%S"),
        "clock": timestamp.strftime("%H:%M"),
        "week": "{:02d}".format(iso_week(day)),
        "hours": hours_text,
    }


def render_journal_entry(
    day,
    timestamp,
    hours_text,
    header_template=DEFAULT_JOURNAL_HEADER,
    entry_template=DEFAULT_JOURNAL_ENTRY,
):
    """
    Render the journal block for one work day.

    Returns:
        Two lines (header and entry), terminated by a newline
    """
    values = journal_values(day, timestamp, hours_text)
    header = _format_template(header_template, DEFAULT_JOURNAL_HEADER, values)
    entry = _format_template(entry_template, DEFAULT_JOURNAL_ENTRY, values)
    return "{}\n{}\n".format(header, entry)


# ---------------------------------------------------------------------------
# Journal file
# ---------------------------------------------------------------------------


def append_journal_entry(path, text):
    """
    Append a block to the journal file, creating file and folder if needed.

    A blank line is inserted so blocks stay separated.

    Raises:
        OSError: If the file cannot be written
    """
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    prefix = ""
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        existing = read_text_file(path)
        if not existing.endswith("\n"):
            prefix = "\n\n"
        elif not existing.endswith("\n\n"):
            prefix = "\n"

    with open(path, "a", encoding="utf-8") as handle:
        handle.write(prefix + text)

    return prefix + text


def journal_entry_marker(day, entry_template=DEFAULT_JOURNAL_ENTRY):
    """
    The part of a journal entry that identifies a day, without the hours.
    """
    values = journal_values(day, datetime(2000, 1, 1), "")
    rendered = _format_template(entry_template, DEFAULT_JOURNAL_ENTRY, values)
    placeholder_start = entry_template.find("{hours}")
    if placeholder_start == -1:
        return rendered.strip()
    prefix_template = entry_template[:placeholder_start]
    return _format_template(prefix_template, prefix_template, values).strip()


def journal_contains_date(path, day, entry_template=DEFAULT_JOURNAL_ENTRY):
    """
    Check whether the journal already holds an entry for that day.

    Returns False when the file does not exist or cannot be read.
    """
    if not os.path.isfile(path):
        return False

    marker = journal_entry_marker(day, entry_template)
    if not marker:
        return False

    try:
        content = read_text_file(path)
    except OSError:
        return False

    return marker in content


def find_journal_hours(path, day, entry_template=DEFAULT_JOURNAL_ENTRY):
    """
    Return the hours already logged for a day, or None if there is no entry.
    """
    if not os.path.isfile(path):
        return None

    marker = journal_entry_marker(day, entry_template)
    if not marker:
        return None

    try:
        content = read_text_file(path)
    except OSError:
        return None

    result = None
    for line in content.splitlines():
        index = line.find(marker)
        if index != -1:
            # Last entry wins, the journal is written chronologically
            result = line[index + len(marker) :].strip() or None
    return result


def describe_session(session, rounding_minutes=DEFAULT_ROUNDING_MINUTES):
    """
    Build the label and description texts for one session.

    Returns:
        Dict with label, description, raw_minutes and rounded_minutes
    """
    day = session.start.date()
    label = "{} {}".format(weekday_abbr(day), session.start.strftime("%H:%M"))

    raw = session_minutes(session)
    if raw is None:
        description = "{} · KW {:02d} · kein Abmelde-Event im Log".format(
            day.strftime("%Y-%m-%d"), iso_week(day)
        )
        return {
            "label": label,
            "description": description,
            "raw_minutes": None,
            "rounded_minutes": None,
        }

    rounded = round_minutes(raw, rounding_minutes)
    if session.running:
        tail = "läuft · bisher {}".format(format_duration(raw))
    else:
        tail = "bis {} · {}".format(session.end.strftime("%H:%M"), format_duration(raw))

    description = "{} · KW {:02d} · {}".format(
        day.strftime("%Y-%m-%d"), iso_week(day), tail
    )
    return {
        "label": label,
        "description": description,
        "raw_minutes": raw,
        "rounded_minutes": rounded,
    }


def parse_int_setting(value, fallback, minimum=None, maximum=None):
    """
    Parse an integer setting, falling back on invalid or out of range values.
    """
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return fallback
    if minimum is not None and number < minimum:
        return fallback
    if maximum is not None and number > maximum:
        return fallback
    return number


def parse_session_key(key):
    """
    Parse the item target of a session back into a datetime.

    The target encodes the start timestamp so the plugin does not have to keep
    state between on_suggest() calls.
    """
    try:
        return datetime.strptime(key, "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        return None


def session_key(session):
    """Stable, unique item target for a session."""
    return session.start.strftime("%Y-%m-%dT%H:%M")


def minutes_between(start, end):
    """Whole minutes between two datetimes, never negative."""
    if start is None or end is None:
        return 0
    return max(int((end - start).total_seconds() // 60), 0)


def add_minutes(moment, minutes):
    """Shift a datetime by minutes."""
    return moment + timedelta(minutes=minutes)
