# KeyPi - Atlassian Query Explorer Plugins

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Keypirinha](https://img.shields.io/badge/Keypirinha-Plugin-blue.svg)](https://keypirinha.com)

> 🚀 Query Jira and Confluence directly from your Keypirinha launcher using JQL and CQL

**KeyPi** is a collection of powerful Keypirinha plugins that bring Atlassian Cloud products into your launcher workflow. Search Jira tickets and Confluence pages without leaving your keyboard.

---

## 📦 Available Plugins

### 🎯 Jira Query Explorer (JQE)
Query Jira Cloud using JQL (Jira Query Language) directly from Keypirinha.

**Key Features:**
- ⚡ Execute JQL queries instantly
- 🔍 Two-phase workflow: Query → Filter results locally
- 💾 JQL Shortcuts for frequently used queries
- 📜 Query History - recall recent queries with #history
- 🎨 Configurable keyword (default: `jqe`)
- 🌐 Open tickets in browser
- 📊 Display: Ticket ID, Status, Summary, Priority, Creator, Assignee

### 🌐 Confluence Query Explorer (CQE)
Query Confluence Cloud using CQL (Confluence Query Language) directly from Keypirinha.

**Key Features:**
- ⚡ Execute CQL queries instantly
- 🔍 Two-phase workflow: Query → Filter results locally
- 💾 CQL Shortcuts for frequently used queries
- 📜 Query History - recall recent queries with #history
- 🎨 Configurable keyword (default: `cqe`)
- 🎯 Multi-Action Support: Open, Copy URL, Edit page (Tab menu)
- 📄 Display: Page title, Space, Type, Last Modified date

### 👤 User Search (US)
Search for users via Jira Cloud API and quickly open Teams chat or user profiles.

**Key Features:**
- ⚡ Search users by name or email
- 🔍 Two-phase workflow: Search → Filter results locally
- 📜 User History - recent users shown while typing
- 💬 Teams Chat integration (sip: protocol)
- 👤 Direct profile access in browser
- 🎨 Configurable keyword (default: `us`)
- 🎯 Multi-Action Support: Teams Chat, Open Profile

### ⏱️ WorkLog (WL)
Turn Windows logon events into working hours and append them to a journal file.

**Key Features:**
- 📅 Lists the recent logon events with weekday, date and calendar week
- ⏱️ Working time from logon to logoff, rounded to 15 minutes
- ☕ Break variants in one keystroke (no break, 1h, 1,5h - configurable)
- 📝 Appends the result to a journal file
- ⚠️ Warns when the day was already logged
- 🎨 Configurable keyword (default: `wl`)
- 🌍 Works offline, no API and no `locale` dependency

**Shared Features:**
- 🔐 Secure API token authentication
- 🔄 Shared Atlassian credentials across plugins
- ⚙️ Easy configuration via INI files
- 🚫 No excessive API calls (smart caching)

---

## 🚀 Quick Start

### Prerequisites
- [Keypirinha](https://keypirinha.com) launcher (Windows)
- Atlassian Cloud account (Jira/Confluence)
- [Atlassian API Token](https://id.atlassian.com/manage-profile/security/api-tokens)

### Installation

1. **Copy plugin folders** to Keypirinha:
   ```
   %APPDATA%\Keypirinha\InstalledPackages\
   ```
   - Copy `keypi_jqe/` for Jira plugin
   - Copy `keypi_cqe/` for Confluence plugin
   - Copy `keypi_us/` for User Search plugin

2. **Create configuration files** in:
   ```
   %APPDATA%\Keypirinha\User\
   ```

3. **Restart Keypirinha**: `Ctrl + Alt + R`

---

## ⚙️ Configuration

### Jira Plugin Configuration

Create: `%APPDATA%\Keypirinha\User\keypi_jqe.ini`

```ini
[main]
# Your Jira Cloud instance URL (without trailing slash)
jira_url = https://your-domain.atlassian.net

# Your Atlassian account email
atlassian_email = your-email@example.com

# Your Atlassian API token
# Create one at: https://id.atlassian.com/manage-profile/security/api-tokens
atlassian_api_key = your-api-token-here

# Keyword to trigger the plugin (default: jqe)
keyword = jqe

# Maximum history entries (default: 30)
history_max_entries = 30

# JQL Shortcuts - Quick access to frequently used queries
[jql_shortcuts]
me = assignee = currentUser()
open = status = "Open"
mytask = assignee = currentUser() AND status = "Open"
```

### Confluence Plugin Configuration

Create: `%APPDATA%\Keypirinha\User\keypi_cqe.ini`

```ini
[main]
# Your Confluence Cloud instance URL (without trailing slash or /wiki)
confluence_url = https://your-domain.atlassian.net

# Your Atlassian account email
atlassian_email = your-email@example.com

# Your Atlassian API token (same as Jira)
atlassian_api_key = your-api-token-here

# Keyword to trigger the plugin (default: cqe)
keyword = cqe

# Maximum history entries (default: 30)
history_max_entries = 30

# CQL Shortcuts - Quick access to frequently used queries
[cqe_shortcuts]
myco = title ~ konzept and creator = currentUser()
recent = lastModified >= now("-7d") ORDER BY lastModified DESC
```

### User Search Plugin Configuration

Create: `%APPDATA%\Keypirinha\User\keypi_us.ini`

```ini
[main]
# Your Jira Cloud instance URL (without trailing slash)
jira_url = https://your-domain.atlassian.net

# Your Atlassian account email
atlassian_email = your-email@example.com

# Your Atlassian API token (same as Jira/Confluence)
atlassian_api_key = your-api-token-here

# Keyword to trigger the plugin (default: us)
keyword = us

# Maximum history entries (default: 30)
history_max_entries = 30
```

**💡 Tip:** You can use the same credentials for all three plugins!

### WorkLog Plugin Configuration

Create: `%APPDATA%\Keypirinha\User\keypi_worklog.ini`

```ini
[main]
# Keyword to trigger the plugin (default: wl)
keyword = wl

# Windows event log export with the logon/logoff events
# Default: <Documents>\logs\winevent.log
winevent_log = C:\Users\YourName\Documents\logs\winevent.log

# Journal file the working hours are appended to
# Default: <Documents>\logs\Journal.log
journal_file = C:\Users\YourName\Documents\logs\Journal.log

# Break variants in minutes (default: 0, 60, 90)
break_options = 0, 60, 90

# Rounding of the working time in minutes (default: 15)
rounding_minutes = 15

# Number of logon events in the list (default: 30)
max_entries = 30

# Wording of the event log, adjust for non-German Windows
event_source = EventLog
event_start_marker = gestartet
event_stop_marker = beendet

# Journal templates
# Placeholders: {weekday} {date} {time} {clock} {week} {hours}
journal_header = # {weekday} {date} {time}
journal_entry = @arbeitsstunden am {date}: {hours}
```

**💡 Note:** WorkLog needs no credentials, it only reads local files.

---

## 💻 Usage

### Jira Query Explorer (JQE)

#### Basic Workflow

1. **Open Keypirinha** and type: `jqe`
2. **Press Tab** to enter query mode
3. **Enter JQL query**: `assignee = currentUser()`
4. **Press Enter** to execute
5. **Filter results** by typing more text
6. **Select ticket** and press Enter to open in browser

#### JQL Shortcuts

Save time with reusable shortcuts for frequent queries!

**Using shortcuts:**
```
jqe → #           # Show all shortcuts
jqe → #me         # Filter shortcuts by name
jqe → #me → Enter # Execute "assignee = currentUser()"
jqe → #edit       # Open config file for editing
```

#### Query History (New in v1.4.0, Virtual Query Mode in v1.5.0)

Access your recently executed queries with `#history` (or `#his`)!

**Using history:**
```
jqe → #history       # Show recent queries (also: #his)
jqe → #history clear # Clear all history
```

**History entry actions:**
- **Tab**: Execute query and show results in Keypirinha (Virtual Query Mode) ✨
- **Enter**: Open JQL search in browser

**Virtual Query Mode (v1.5.0):**
Select a history entry and press Tab to instantly see the Jira results - no need to re-type the query! You can then filter the results by typing and select a ticket to open.

**Features:**
- Automatically saves executed queries
- Configurable max entries (default: 30)
- Duplicates move to top (no duplicates in list)
- Persistent across Keypirinha restarts

**Example queries:**
```jql
assignee = currentUser()
project = MYPROJECT AND status = "Open"
assignee = currentUser() AND status = "Open" ORDER BY priority DESC
filter = 12345
```

📚 [JQL Documentation](https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/)

---

### Confluence Query Explorer (CQE)

#### Basic Workflow

1. **Open Keypirinha** and type: `cqe`
2. **Press Tab** to enter query mode
3. **Enter CQL query**: `type=page AND space=MYSPACE`
4. **Press Enter** to execute
5. **Filter results** by typing more text
6. **Select page**:
   - **Press Enter** to open in browser
   - **Press Tab** to see action menu (Open, Copy URL, Edit page)

#### CQL Shortcuts (New in v1.2.0)

Save time with reusable shortcuts for frequent queries!

**Using shortcuts:**
```
cqe → #           # Show all shortcuts
cqe → #myco       # Filter shortcuts by name
cqe → #myco → Enter # Execute the CQL query
cqe → #edit       # Open config file for editing
```

**Define shortcuts in config:**
```ini
[cqe_shortcuts]
myco = title ~ konzept and creator = currentUser()
mytodo = title ~ todo and creator = currentUser()
recent = lastModified >= now("-7d") ORDER BY lastModified DESC
```

#### Query History (New in v1.3.0)

Access your recently executed queries with `#history` (or `#his`)!

**Using history:**
```
cqe → #history       # Show recent queries (also: #his)
cqe → #history clear # Clear all history
```

**History entry actions:**
- **Tab**: Execute query and show results in Keypirinha (Virtual Query Mode) ✨
- **Enter**: Open CQL search in browser

**Virtual Query Mode:**
Select a history entry and press Tab to instantly see the Confluence results - no need to re-type the query! You can then filter the results by typing and select a page to open.

**Features:**
- Automatically saves executed queries
- Configurable max entries (default: 30)
- Duplicates move to top (no duplicates in list)
- Persistent across Keypirinha restarts

#### Multi-Action Menu (New in v1.1.0)

Each search result offers multiple actions via Tab:

1. **Open page** - Open page in browser (view mode) - Default action with Enter
2. **Copy URL** - Copy page URL to clipboard
3. **Edit page** - Open page directly in edit mode

**Usage:**
- Select page → **Tab** → Action menu appears
- Select action → **Enter** → Action executes

#### Example queries:
```cql
# All pages in a space
type=page AND space=MYSPACE

# Search by title
type=page AND title~"Setup"

# Recent pages
type=page AND created >= "2025/01/01"

# Combined conditions
type=page AND space=DOC AND title~"API"
```

📚 [CQL Documentation](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)

---

### User Search (US)

#### Basic Workflow

1. **Open Keypirinha** and type: `us`
2. **Press Tab** to enter search mode
3. **Enter name**: `Max`
4. **Press Tab** to execute search (or Enter if no history matches)
5. **Filter results** by typing more text
6. **Select user**:
   - **Press Enter** to open Teams Chat (default)
   - **Press Tab** to see action menu (Teams Chat, Open Profile)

#### User History (New in v1.1.0)

Access your recently used users directly while typing!

**Using history:**
```
us → max           # Shows history entries matching "max" + API search option
us → #history      # Show all history entries (Tab to show)
us → #history clear # Clear all history
```

**Features:**
- History entries shown while typing (with [History] prefix)
- "Tab/Enter: API-Suche starten" option always at bottom
- Configurable max entries (default: 30)
- Duplicates move to top (no duplicates in list)
- Persistent across Keypirinha restarts

#### Multi-Action Menu

Each user result offers multiple actions via Tab:

1. **Open Profile** - Open Jira user profile in browser
2. **Teams Chat** - Open MS Teams chat with user (default action with Enter)

**For users without email:**
- Teams Chat shows: "nicht möglich - keine E-Mail"
- Default action opens Profile instead

**Usage:**
- Select user → **Tab** → Action menu appears
- Select action → **Enter** → Action executes

### WorkLog (WL)

#### Basic Workflow

1. **Open Keypirinha** and type: `wl`
2. **Press Tab** to list the recent logon events:
   ```
   Mi 09:04    2026-08-19 · KW 34 · bis jetzt 17:09 · 8h 05m
   Di 08:10    2026-08-18 · KW 34 · bis 17:28 · 9h 18m
   ```
3. **Press Tab** on an entry to see the working time variants:
   ```
   8h · ohne Pause      09:04-17:09 · 8h 00m gerundet
   7h · 1h Pause        09:04-17:09 · 8h 00m gerundet minus 1h
   6,5h · 1,5h Pause    09:04-17:09 · 8h 00m gerundet minus 1,5h
   ```
4. **Press Enter** to append the entry to the journal file:
   ```
   # Mi 2026-08-19 1709:44
   @arbeitsstunden am 2026-08-19: 7h
   ```

#### How the working time is calculated

Every logon event is its own entry. The session ends

- at the **current time** for every logon of **today**
- at the **last** logoff event of that day for past days
- at the next logoff event in the log when the day ended after midnight

The **difference** is rounded to the nearest 15 minutes, not the start and end
separately: 09:04 to 17:09 is 8h05m and becomes 8h. The break is subtracted
afterwards.

**Reboot during the day:** a restart writes a logoff and a logon event, so the
day shows up twice. Both entries count up to the current time - pick the one
the working day actually started with.

#### Multi-Action Menu

1. **Write journal entry** - append to the journal file (default action)
2. **Copy entry to clipboard** - copy instead of write

#### Shortcuts

```
wl → #edit      # Open the configuration file
wl → #journal   # Open the journal file
wl → #source    # Open the event log export
```

#### Producing the event log export

WorkLog reads a text export of the Windows event log, newest entry first:

```
   35735 Aug 19 09:04  Information EventLog   2147489653 Der Ereignisprotokolldienst wurde gestartet.
   35724 Aug 18 17:28  Information EventLog   2147489654 Der Ereignisprotokolldienst wurde beendet.
```

Any scheduled export that produces this layout works. Lines from other event
sources are ignored, even when they contain the same wording.

---

## 🎨 Features in Detail

### Two-Phase Workflow
Both plugins use a smart two-phase workflow to minimize API calls:

1. **Phase 1: Query Mode**
   - Type your JQL/CQL query
   - No API calls while typing
   - Press Enter to execute

2. **Phase 2: Filter Mode**
   - Results are cached locally
   - Filter instantly without additional API calls
   - Keypirinha's native filtering for smooth UX

**Benefits:**
- 🚀 90% fewer API calls
- ⚡ Lightning-fast filtering
- 🔋 Respects API rate limits

### JQL Shortcuts (JQE only)

Create shortcuts for frequently used queries:

```ini
[jql_shortcuts]
# Personal queries
me = assignee = currentUser()
myopen = assignee = currentUser() AND status = "Open"

# Team queries
team = project = MYPROJECT AND sprint in openSprints()

# Custom queries
critical = priority = Highest AND status != "Done"
```

**Features:**
- Case-insensitive matching
- Quick access with `#` prefix
- Edit shortcuts with `#edit` command
- Share configs across devices

---

## 🔧 Troubleshooting

### "Configuration missing" error
- ✅ Check if INI file exists in `%APPDATA%\Keypirinha\User\`
- ✅ Verify all required fields are filled (URL, email, API token)
- ✅ Restart Keypirinha with `Ctrl + Alt + R`

### "Authentication failed" error
- ✅ Verify API token is correct
- ✅ Check email address matches your Atlassian account
- ✅ Ensure URL has no trailing slash
- ✅ For Confluence: URL should NOT include `/wiki`

### "No results found"
- ✅ Check your JQL/CQL syntax
- ✅ Verify you have access to the project/space
- ✅ Test query in Jira/Confluence web UI first

### View Logs
- Press `F2` in Keypirinha to open console
- Check for error messages and debug info

---

## 📋 Limits & Performance

| Feature | JQE | CQE | US |
|---------|-----|-----|-----|
| Max results per query | 50 | 50 | 50 |
| Request timeout | 10s | 10s | 10s |
| API calls while filtering | 0 | 0 | 0 |
| Supported platforms | Windows | Windows | Windows |

---

## 🔒 Security

- 🔐 API tokens stored locally in plain text INI files
- ⚠️ Keep your API tokens secure - treat them like passwords
- 🚫 Never commit INI files with credentials to version control
- 🔄 Rotate tokens regularly at [Atlassian Account Security](https://id.atlassian.com/manage-profile/security/api-tokens)

---

## 📝 Changelog

### Jira Query Explorer v1.5.0 (2026-01-29)
- ✨ **Virtual Query Mode** - Tab on history entry executes query and shows results
- 🚀 Seamless workflow: `#history` → Tab → See results → Filter → Open ticket
- 🔄 Changed history entry behavior: Tab shows results, Enter opens browser
- ✅ 8 new unit tests for Virtual Query Mode

### Jira Query Explorer v1.4.0 (2026-01-27)
- ✨ Query History - recall recent queries with `#history` (or `#his`)
- ✨ History Actions: Copy JQL (default) or open in browser
- ✨ `#history clear` to delete all history
- 💾 Persistent history across restarts (JSON file)
- ⚙️ Configurable max history entries (default: 30)
- 🔄 Duplicate queries move to top
- ✅ 24 unit tests for history functionality

### Jira Query Explorer v1.2.0 (2025-12-22)
- ✨ JQL Shortcuts for frequently used queries
- ✨ # prefix for shortcut access
- ✨ #edit command to open config file
- ✨ List all shortcuts with #
- 🎨 Case-insensitive shortcut matching

### Jira Query Explorer v1.1.0 (2025-12-19)
- ✨ Two-Phase Filter Mode (JQL Input → Filter Results)
- ✨ Configurable keyword
- 🚀 No API calls during JQL input
- ⚡ 90% fewer API calls

### Jira Query Explorer v1.0.0 (2025-12-18)
- 🎉 Initial release
- ✨ JQL query execution
- ✨ Display tickets with key info
- ✨ Open tickets in browser

### Confluence Query Explorer v1.3.0 (2026-02-03)
- ✨ **Query History** - recall recent queries with `#history` (or `#his`)
- ✨ **Virtual Query Mode** - Tab on history entry executes query and shows results
- ✨ `#history clear` to delete all history
- 💾 Persistent history across restarts (JSON file)
- ⚙️ Configurable max history entries (default: 30)
- 🔄 Duplicate queries move to top
- ✅ 32 unit tests for history functionality

### Confluence Query Explorer v1.2.0 (2026-01-26)
- ✨ CQL Shortcuts for frequently used queries
- ✨ # prefix for shortcut access
- ✨ #edit command to open config file
- ✨ List all shortcuts with #
- 🎨 Case-insensitive shortcut matching

### Confluence Query Explorer v1.1.0 (2026-01-23)
- ✨ Multi-Action Support (Tab menu)
  - Open page (default)
  - Copy URL to clipboard
  - Edit page (opens edit mode directly)
- 📊 Enhanced result display: Space, Type, Last Modified date
- 🚀 API expand parameter for full data
- ✅ 15 unit tests for reliability

### Confluence Query Explorer v1.0.0 (2025-01-21)
- 🎉 Initial release
- ✨ CQL query execution
- ✨ Two-Phase Filter Mode
- ✨ Configurable keyword
- ✨ Open pages in browser
- 🔗 Shared credentials with JQE

### User Search v1.1.0 (2026-02-05)
- ✨ **User History** - Recent users shown while typing
- ✨ Filtered history with `[History]` prefix
- ✨ `#history clear` to delete all history
- 💾 Persistent history across restarts (JSON file)
- ⚙️ Configurable max history entries (default: 30)
- 🔄 Duplicate users move to top

### User Search v1.0.0 (2026-02-05)
- 🎉 Initial release
- ✨ User search via Jira Cloud API
- ✨ Two-Phase Filter Mode
- ✨ Multi-Action Support (Teams Chat, Open Profile)
- ✨ `#edit` shortcut to open config
- 💬 Teams Chat integration via sip: protocol
- 🔗 Shared credentials with JQE/CQE

---

## 🛣️ Roadmap

See [BACKLOG.md](BACKLOG.md) for planned features and ideas:
- Pagination support (>50 results)
- Custom field display
- Multi-instance support
- Status indicators with colors/icons
- Ticket actions (status changes, comments)

---

## 🤝 Contributing

This is a personal project, but suggestions and bug reports are welcome!

- 🐛 Report bugs in [Issues](https://github.com/jerik/keypi/issues)
- 💡 Feature requests in [BACKLOG.md](BACKLOG.md)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Credits

- Built for [Keypirinha](https://keypirinha.com) launcher
- Uses [Atlassian Cloud REST APIs](https://developer.atlassian.com/cloud/)
- Inspired by the need for keyboard-driven workflows

---

## 📚 Documentation

- **User Guide**: [documentation.md](documentation.md) - Detailed usage guide (German)
- **Development**: [CLAUDE.md](CLAUDE.md) - Project rules & development workflow
- **Backlog**: [BACKLOG.md](BACKLOG.md) - Feature ideas & known issues

---

**Made with ⌨️ for Keypirinha users**

[⬆ Back to top](#keypi---atlassian-query-explorer-plugins)
