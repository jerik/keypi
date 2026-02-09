# KeyPi - Development Best Practices

Quick reference for building new Keypirinha plugins in this project.
For full details see `KEYPIRINHA-LEARNINGS.md`.

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

---

## Testing

- Tests in `tests/test_<name>.py`
- Copy filter/parsing logic into test for isolated testing
- Run: `pytest` from project root
- Lint: `ruff check .` and `ruff format --check .`

---

## Version Policy

- Dev: `VERSION = "1.0.0-dev.1"` (increment per commit)
- Release: `VERSION = "1.0.0"` (remove -dev suffix)
