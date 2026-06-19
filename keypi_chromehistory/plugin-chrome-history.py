import fileinput
import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet
import os
import re
import textwrap
import csv


class chrome_history(kp.Plugin):
    """
    lookup the chrome history
    """

    CHROME_HIST_CAT = kp.ItemCategory.USER_BASE + 10  # for the actions

    # for the actions
    OPEN_URL_NAME = "open url"
    OPEN_URL_LABEL = "Open URL"

    COPY_URL_NAME = "copy url"
    COPY_URL_LABEL = "Copy url"

    _box = []  
    _conn = None

    def __init__(self):
        super().__init__()

    # jerik:0 is not regulary executed every keypirinha keystroke
    def _read_config(self):
        settings = self.load_settings()

        # It's the folder FOLDERID_Documents ("%USERPROFILE%\Documents")
        # https://docs.microsoft.com/sv-se/windows/win32/shell/knownfolderid?redirectedfrom=MSDN
        default_path = kpu.shell_known_folder_path(
            "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"
        )
        self._filepath = settings.get_stripped(
            "file_path", "main", default_path
        )

        # jerik:1 specifiy file/database location
        self._roots = [
                r'C:\Users\e17\Documents',
                r'C:\Users\e17\Pictures',
                r'C:\Users\e17'
                ]
        self._directories = []
        self._source_csv = r'c:\users\e17\documents\clean-history.csv'

    def on_start(self):
        self._debug = False # jerik
        self._read_config()

        # Added own action for file selection. 
        self.set_actions(self.CHROME_HIST_CAT, [
            self.create_action(
                name=self.COPY_URL_NAME,
                label=self.COPY_URL_LABEL,
                short_desc="Copy URL"
            ),
            self.create_action(
                name=self.OPEN_URL_NAME,
                label=self.OPEN_URL_LABEL,
                short_desc="Lookup Chrome history"
            )
        ])


    # jerik: is excuted after the plugin is loaded. Periodically
    def on_catalog(self):
        catalog = []

        catalog.append(self.create_item(
            category=kp.ItemCategory.KEYWORD,
            label="ch",
            short_desc="Browser history lookup",
            target="ch",
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.KEEPALL
        ))
        # self.info("-----------") # jerik

        self.set_catalog(catalog)

    # jerik:2 is executed when the keyword of the catalog is called
    def on_suggest(self, user_input, items_chain):
        self._get_entries()

        if not items_chain:
            return

        suggestions = self._box[:]
        # self.info('info:: ', suggestions)


        # @todo check doku https://keypirinha.com/api/catalogitem.html
        # accepts_args()
        # loop_on_suggest()


        if user_input:
            target = user_input.strip().format(q=user_input.strip())
            # self.info('User input: ', user_input)

        # self.set_suggestions(suggestions, kp.Match.DEFAULT, kp.Sort.NONE)
        self.set_suggestions(
            suggestions,
            kp.Match.ANY if not user_input else kp.Match.FUZZY,
            kp.Sort.NONE if not user_input else kp.Sort.SCORE_DESC,
        )

    def on_execute(self, item, action):

        # Create the actions for the selected entry
        if item and item.category() == self.CHROME_HIST_CAT: 
            if not action: 
                #self.info("::: no action") 
                #self.info(item.short_desc())
                kpu.web_browser_command(url=item.short_desc(), execute=True)
            if action and action.name() == self.OPEN_URL_NAME: 
                #self._open_folder(item.short_desc())
                kpu.web_browser_command(url=item.short_desc(), execute=True)
            if action and action.name() == self.COPY_URL_NAME: 
                kpu.set_clipboard(item.short_desc())

        #self.info("item in on_execute: ", item, "category:", item.category())
        # If you select no action, but hit only enter on the entry, there is no action
        #if action: 
            #self.info("action in on_execute: ", action, ":name:", action.name())

    def _open_folder(self, path): 
        command = f'cmd /K start {path}'
        DETACHED_PROCESS = 0x00000008
        subprocess.call(command, creationflags=DETACHED_PROCESS)
        # self.info(f'into _call_teams:::::: {command}')

    # jerik:0 is executed when keypirinha is called with keystroke
    def on_activated(self):
        pass

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self._read_config()


    # jerik:3
    def _get_entries(self): 

        with open(self._source_csv, encoding="utf8" ) as file: 
            data = list(csv.reader(file, delimiter=';'))

        # clear box
        self._box = []
        # Add files to keypirinha, that I can choose from ist
        for item in data:
            #self.info(item)
            # remove {} in item[0] 
            item[0] = re.sub(r"[{}]", "", item[0])
            self._box.append(self._create_suggestion_hist( item ))


    def _create_suggestion_hist(self, item):

        title = item[0]
        url = item[1]

        # if title contains a {, then the plugin does not work
        if '{' in title: 
            # self.info('B'*20)
            self.info(item)

        text = textwrap.wrap(title, width=70)
        label = text.pop(0)
        desc = url

        return self.create_item(
            category=self.CHROME_HIST_CAT,
            label=label,
            short_desc="".join(desc),
            target=title.strip().format(q=title.strip()),  # has problems with { in title
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE,
        )
