import fileinput
import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet
import os
import re
import textwrap
import subprocess
from datetime import datetime, date
import locale


class file_lookup(kp.Plugin):
    """
    foo plugin for experiments
    """

    DIR_CAT = kp.ItemCategory.USER_BASE + 10  # for the actions

    # for the actions
    OPEN_BOOKMARK = "open_bookmark"
    OPEN_BOOKMARK_LABEL = "Open bookmark"

    OPEN_COPY_NAME = "copy_bookmark"
    OPEN_COPY_LABEL = "Copy bookmark"

    _box = []  
    _bookmarks = []

    def __init__(self):
        super().__init__()

    # jerik:0 is not regulary executed every keypirinha keystroke
    def _read_config(self):
        settings = self.load_settings()
        #self.info('settings: : : :')
        #self.info(settings.keys('files'))
        self.get_textfiles(settings)
        # self._textfiles = settings.keys('files')

        # It's the folder FOLDERID_Documents ("%USERPROFILE%\Documents")
        # https://docs.microsoft.com/sv-se/windows/win32/shell/knownfolderid?redirectedfrom=MSDN
        default_path = kpu.shell_known_folder_path(
            "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"
        )
        self._filepath = settings.get_stripped(
            "file_path", "main", default_path
        )

        # jerik:1 specifiy file/database location
        # OLD see: OLD_get_filecontent(self): 
        self._file = self._filepath + '\\test.txt'

        self._directories = []


    def get_textfiles(self, setting): 
        self._textfiles = []
        #self.info('*'*23)
        for key in setting.keys('files'): 
            item = setting.get(key, 'files')
            self._textfiles.append({'key': key, 'path': item })

    def on_start(self):
        self._debug = False # jerik
        self._read_config()

        # Added own action for file selection. 
        self.set_actions(self.DIR_CAT, [
            self.create_action(
                name=self.OPEN_BOOKMARK,
                label=self.OPEN_BOOKMARK_LABEL,
                short_desc="Open Directory in Fileexplorer"
            ),
            self.create_action(
                name=self.OPEN_COPY_NAME,
                label=self.OPEN_COPY_LABEL,
                short_desc=""
            )
        ])


    # jerik: is excuted after the plugin is loaded. Periodically
    def on_catalog(self):
        catalog = []

        catalog.append(self.create_item(
            category=kp.ItemCategory.KEYWORD,
            label="fl",
            short_desc="File lookup",
            target="fl",
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.KEEPALL
        ))
        # self.info("-----------") # jerik

        self.set_catalog(catalog)

    # jerik:2 is executed when the keyword of the catalog is called
    def on_suggest(self, user_input, items_chain):
        self._get_filecontent()

        # self.info('item chain:') 
        # self.info(items_chain) 

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
        if item and item.category() == self.DIR_CAT: 
            if not action: 
                self.info("::: no action") 
                self._open_folder(item.short_desc())
            if action and action.name() == self.OPEN_BOOKMARK: 
                self._open_folder(item.short_desc())
            if action and action.name() == self.OPEN_COPY_NAME: 
                self._open_cmd_folder(item.short_desc())

        self.info("item in on_execute: ", item, "category:", item.category())
        # If you select no action, but hit only enter on the entry, there is no action
        if action: 
            self.info("action in on_execute: ", action, ":name:", action.name())

    def _open_folder(self, path): 
        command = f'cmd /K start {path}'
        DETACHED_PROCESS = 0x00000008
        subprocess.call(command, creationflags=DETACHED_PROCESS)
        # self.info(f'into _call_teams:::::: {command}')

    def _open_cmd_folder(self, path): 
        command = f'cmd /K cd {path}'
        subprocess.call(command)

    # jerik:0 is executed when keypirinha is called with keystroke
    def on_activated(self):
        pass

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self._read_config()


    # jerik:3
    def _get_filecontent(self): 

        if len(self._textfiles) == 1: 
            textfile = self._textfiles[0]['path']

        bix = []
        with open(textfile, mode='r', encoding='utf-8') as file: 
            lines = file.readlines()
            for line in lines[:30]: 
                if 'gestartet' in line: 
                    # self.info('line: ' +  line)
                    monthday, _ = line.split('Information',1)
                    # self.info('bookmark content: ' + str(len(bookmark)))
                    self.getday(monthday[9:15]) 
                    # self.until_now(monthday[16:])
                    week, weekday = self.getday(monthday[9:15])
                    headline = weekday + ' ' + monthday[16:]
                    bix.append({'headline': headline, 'content': monthday[9:15] + ' #' + week + ' gestartet'})
                    # bix.append({'headline': monthday[9:], 'content': monthday + ' gestartet'})

        # clear box
        self._box = []
        # Add files to keypirinha, that I can choose from ist
        for item in bix: 
            self._box.append(self._create_bookmark( item ))

    # @todo
    def round_quater(minute): 
        if minute < 8: 
            return 0
        elif minute > 7 and minute < 23:
            return 15
        elif minute > 22 and minute < 37:
            return 30
        elif minute > 37 and minute <=53: 
            return 45
        else: 
            return 0
    # @todo
    def until_now(self, monthday): 
        ts = datetime.now()
        hour, minute = monthday.split(':')
        # start = ts.replace(hour=int(hour), minute=int(minute))
        # state = "nice" if is_nice else "not nice"
        start = ts.replace(hour=7, minute=minute)

        # datetime_str = f"{monthday} {date.today().year}" 
        #dt = datetime.strptime(datetime_str, '%b %d %Y')
        diff = ts - start
        # self.info(ts)
        # self.info(start)
        # self.info('#'*23)
        # self.info(diff)

    def getday(self, monthday): 
        locale.setlocale(locale.LC_TIME, "de_DE") # german dateformatings
        datetime_str = f"{monthday} {date.today().year}" 
        dt = datetime.strptime(datetime_str, '%b %d %Y')
        return [dt.strftime('%V'), dt.strftime('%a')]

    def OLD_get_filecontent(self): 

        bix = []
        with open(self._file, mode='r', encoding='utf-8') as file: 
            lines = file.readlines()
            washeadline = False
            for line in lines: 
                if '# ' in line: 
                    # self.info('line: ' +  line)
                    _, headline = line.split(' ',1)
                    washeadline = True
                    # self.info('bookmark content: ' + str(len(bookmark)))
                elif washeadline: 
                    washeadline = False
                    bix.append({'headline': headline, 'content': line})
        # clear box
        self._box = []
        # Add files to keypirinha, that I can choose from ist
        for item in bix: 
            self._box.append(self._create_bookmark( item ))


    def _create_bookmark(self, item):
        # self.info(item)

        text = textwrap.wrap(item['headline'], width=50)
        label = text.pop(0)
        desc = item['content']

        return self.create_item(
            category=self.DIR_CAT,
            label=label,
            short_desc="".join(desc),
            target=item['content'].strip().format(q=item['headline'].strip()),
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE,
            # icon_handle=self.load_icon("res://"+self.package_full_name()+"/stopuhr-blue.ico"),

        )
