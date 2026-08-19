# KeyPi - Development Best Practices

Quick reference for building new Keypirinha plugins in this project.
For full details see `KEYPIRINHA-LEARNINGS.md`.

## Plugins in this repository

| Package | Keyword | Purpose | Data source |
|---------|---------|---------|-------------|
| `keypi_jqe` | `jqe` | Jira search via JQL | Jira Cloud REST API |
| `keypi_cqe` | `cqe` | Confluence search via CQL | Confluence Cloud REST API |
| `keypi_us` | `us` | User search | Jira Cloud REST API |
| `keypi_mindbox` | `mb` | Open local `.mb` files | Local folder |
| `keypi_pmb` | `pmb` | Knowledge graph search | Local SQLite + markdown |
| `keypi_worklog` | `wl` | Log working hours | Local text files |

---

## Plugin Structure

```
keypi_<name>/
├── __init__.py          # Plugin main class (inherits kp.Plugin)
├── lib/
│   ├── __init__.py      # Package marker
│   └── <client>.py      # API client (if needed)
└── res/
    ├── keypi_<name>.ini # Config template
    ├── packages.json    # Package metadata (optional)
    └── changelog/
        └── X.Y.Z.md    # Version changelogs
```

---

## Layering: Plugin Class vs. lib/

The plugin class does **UI wiring only**: config, items, actions, logging.
Everything else lives in `lib/` and must **not import keypirinha**, so it can
be unit tested without the launcher.

| Belongs in `__init__.py` | Belongs in `lib/` |
|--------------------------|-------------------|
| `on_start`, `on_catalog`, `on_suggest`, `on_execute`, `on_events` | Parsing, filtering, formatting |
| `create_item`, `set_suggestions`, `set_actions` | API and file access |
| Reading the INI | Validating INI values |
| `self.info/warn/err` | Pure functions, no side effects |

```python
# keypi_worklog/__init__.py
from .lib import worklog          # only place that knows keypirinha
```

---

## Required Plugin Methods

```python
class MyPlugin(kp.Plugin):
    VERSION = "1.0.0-dev.1"

    def on_start(self):      # Plugin loaded - register actions, log version
    def on_catalog(self):    # Register keyword in catalog
    def on_suggest(self, user_input, items_chain):  # Handle user input
    def on_execute(self, item, action):             # Execute selected item
    def on_events(self, flags):                     # Handle config changes
```

---

## Item Categories

Define distinct categories per item type using `kp.ItemCategory.USER_BASE + N`:

```python
ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1    # Keyword entry
ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2   # Results
ITEMCAT_SHORTCUT = kp.ItemCategory.USER_BASE + 3 # #edit, #history etc.
```

---

## Key Patterns

### State Machine (Two-Phase)
- **Phase 1** (Input): User types, NO API/heavy calls
- **Phase 2** (Filter): Results cached, local filtering only

### Config Loading
```python
def _load_config(self):
    settings = self.load_settings()
    self._keyword = settings.get_stripped("keyword", section="main", fallback="mb")
    # Refresh catalog on keyword change
    if old_keyword != self._keyword:
        self.on_catalog()
```

### #edit Shortcut (every plugin has this)
```python
if user_input.strip().startswith("#"):
    # Handle #edit -> opens config file
    self._handle_shortcut_input(user_input.strip())
```

### Opening Config File
```python
plugin_dir = os.path.dirname(__file__)
config_path = os.path.join(plugin_dir, "..", "..", "User", "keypi_<name>.ini")
config_path = os.path.abspath(config_path)
kpu.shell_execute(config_path)
```

---

## Item Hints Quick Reference

| Hint | Use Case |
|------|----------|
| `args_hint=REQUIRED` | Keyword entry (needs user input) |
| `args_hint=FORBIDDEN` | Final items (no further input) |
| `args_hint=ACCEPTED` | Chainable items (Tab adds to chain) |
| `hit_hint=NOARGS` | Catalog keyword |
| `hit_hint=IGNORE` | Standard actionable item |
| `hit_hint=KEEPALL` | Keep Launchbox open after selection |

---

## Actions (Tab Menu)

Register in `on_start()`, handle in `on_execute()`:

```python
def on_start(self):
    self.set_actions(self.ITEMCAT_RESULT, [
        self.create_action(name="open", label="Open", short_desc="..."),
        self.create_action(name="copy", label="Copy URL", short_desc="..."),
    ])

def on_execute(self, item, action):
    if not action:  # Default action (Enter)
        ...
    elif action.name() == "copy":
        kpu.set_clipboard(url)
```

---

## Critical Rules

1. **NEVER block UI** in `on_suggest()` - no slow I/O or API calls
2. **set_suggestions() does NOT work** in `on_execute()` - Launchbox closes
3. **Unique targets** per item (Keypirinha deduplicates same targets)
4. **Config changes** need `on_catalog()` call to refresh keyword
5. **loop_on_suggest=True** needed for Tab-chaining (Virtual Query Mode)
6. **Never call `locale.setlocale()`** - it is process wide and hits every plugin
7. **Every INI value is user input** - parse defensively, always keep a fallback
8. **Pass state via `data_bag`** (JSON), never via instance lists indexed by position

---

## Testing

- Tests in `tests/test_<name>.py`, fixtures in `tests/fixtures/`
- Run: `pytest` from project root
- Lint: `ruff check .` and `ruff format --check .`

### Testing lib/ logic (preferred)

Load the module by path - no keypirinha needed, no copied code:

```python
_SPEC = importlib.util.spec_from_file_location(
    "worklog", os.path.join(REPO_ROOT, "keypi_worklog", "lib", "worklog.py")
)
worklog = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(worklog)
```

❌ Don't copy the implementation into the test file - the copy drifts away
from the original (older tests in this repo still do this).

### Testing the plugin class

Register a keypirinha stub in `sys.modules` **before** importing the package,
see `tests/test_worklog_plugin.py`:

```python
kp = types.ModuleType("keypirinha")
kp.Plugin = _Plugin        # fake base class: load_settings, set_suggestions, ...
kp.ItemCategory = types.SimpleNamespace(USER_BASE=100, KEYWORD=1)
sys.modules["keypirinha"] = kp     # overwrite, do not setdefault
```

⚠️ Several test modules stub keypirinha. Using `setdefault` makes the result
depend on pytest's import order - tests pass alone and fail in the full run.
One stub has to be a superset and always win.

### Fixtures with personal data

Never commit the user's real files. Generate a fixture with the same layout
and synthetic content, add the real file to `.gitignore`, and build the edge
cases into the fixture deliberately.

---

## Version Policy

- Dev: `VERSION = "1.0.0-dev.1"` (increment per commit)
- Release: `VERSION = "1.0.0"` (remove -dev suffix)
