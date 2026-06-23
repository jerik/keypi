"""
Keypirinha Plugin: Chrome History
Search Chrome browser history directly from the Keypirinha launcher.
"""

import csv
import os

try:
    import keypirinha as kp
    import keypirinha_util as kpu

    _KEYPIRINHA_AVAILABLE = True
except ImportError:
    # Outside Keypirinha runtime (tests, linting). Provide minimal stubs.
    import types

    _stub = types.SimpleNamespace
    kp = _stub(  # type: ignore[assignment]
        Plugin=object,
        ItemCategory=_stub(KEYWORD=0, USER_BASE=1000),
        ItemArgsHint=_stub(REQUIRED=0, FORBIDDEN=1, ACCEPTED=2),
        ItemHitHint=_stub(KEEPALL=0, IGNORE=1),
        Match=_stub(ANY=0, FUZZY=1),
        Sort=_stub(NONE=0, SCORE_DESC=1),
        Events=_stub(PACKCONFIG=1),
    )
    kpu = _stub(web_browser_command=lambda **_: None, set_clipboard=lambda _: None)  # type: ignore[assignment]
    _KEYPIRINHA_AVAILABLE = False


class ChromeHistory(kp.Plugin):
    """Search Chrome browser history from Keypirinha."""

    VERSION = "1.0.0-dev.5"

    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 1

    ACTION_OPEN_URL = "open_url"
    ACTION_COPY_URL = "copy_url"

    _keyword = "ch"
    _csv_path = ""

    def on_start(self):
        self._read_config()
        self.set_actions(
            self.ITEMCAT_RESULT,
            [
                self.create_action(
                    name=self.ACTION_OPEN_URL,
                    label="Open in browser",
                    short_desc="Open URL in default browser",
                ),
                self.create_action(
                    name=self.ACTION_COPY_URL,
                    label="Copy URL",
                    short_desc="Copy URL to clipboard",
                ),
            ],
        )

    def on_catalog(self):
        self.set_catalog(
            [
                self.create_item(
                    category=kp.ItemCategory.KEYWORD,
                    label=self._keyword,
                    short_desc="Search Chrome browser history",
                    target=self._keyword,
                    args_hint=kp.ItemArgsHint.REQUIRED,
                    hit_hint=kp.ItemHitHint.KEEPALL,
                )
            ]
        )

    def on_suggest(self, user_input, items_chain):
        if not items_chain:
            return

        entries = self._load_csv()
        if not entries:
            self.set_suggestions(
                [
                    self.create_error_item(
                        label="No Chrome history found",
                        short_desc=(
                            f"Run chrome_history_preprocess.py first. "
                            f"Expected CSV: {self._csv_path}"
                        ),
                    )
                ]
            )
            return

        suggestions = [
            self.create_item(
                category=self.ITEMCAT_RESULT,
                label=entry["title"] or entry["url"],
                short_desc=entry["url"],
                target=f"ch_{idx}",
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.IGNORE,
                data_bag=entry["url"],
            )
            for idx, entry in enumerate(entries)
        ]

        self.set_suggestions(
            suggestions,
            kp.Match.ANY if not user_input else kp.Match.FUZZY,
            kp.Sort.NONE if not user_input else kp.Sort.SCORE_DESC,
        )

    def on_execute(self, item, action):
        if item.category() != self.ITEMCAT_RESULT:
            return
        url = item.data_bag()
        if not action or action.name() == self.ACTION_OPEN_URL:
            kpu.web_browser_command(url=url, execute=True)
        elif action.name() == self.ACTION_COPY_URL:
            kpu.set_clipboard(url)

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self._read_config()
            self.on_catalog()

    def _read_config(self):
        settings = self.load_settings()
        self._keyword = settings.get_stripped("keyword", "main", fallback="ch")
        default_csv = os.path.join(
            os.environ.get("USERPROFILE", ""),
            "Documents",
            "tmp",
            "chrome-history-clean.csv",
        )
        raw_path = settings.get_stripped("csv_path", "main", fallback=default_csv)
        self._csv_path = os.path.expandvars(raw_path)

    def _load_csv(self) -> list:
        if not os.path.exists(self._csv_path):
            self.warn(f"CSV not found: {self._csv_path}")
            return []
        try:
            entries = []
            with open(self._csv_path, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                for row in reader:
                    if len(row) >= 2:
                        entries.append({"title": row[0], "url": row[1]})
            return entries
        except Exception as e:
            self.err(f"Failed to read CSV: {e}")
            return []
