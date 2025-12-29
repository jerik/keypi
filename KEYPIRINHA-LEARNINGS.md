# Keypirinha Plugin Development - Lessons Learned

**Purpose**: Best Practices, Pitfalls, and Insights for Keypirinha Plugin Development
**Audience**: Claude (primary), Erik (contributor)
**Updated**: 2025-12-22

---

## 🎯 API Best Practices

### State Management
- ✅ **DO**: Use instance variables for persistent state tracking
  ```python
  self._current_mode = "jql"  # Tracks current plugin mode
  self._cached_results = []   # Stores API results for filtering
  ```
- ❌ **DON'T**: Store state in suggestion items (they're regenerated frequently)
- 💡 **Lesson (v1.1.0)**: State machine pattern (`MODE_JQL` vs `MODE_FILTER`) works cleanly for multi-phase workflows

### Suggestion Updates
- ✅ **DO**: Call `set_suggestions()` whenever plugin state changes
- ✅ **DO**: Keep `on_suggest()` lightweight and fast (it's called on every keystroke)
- ❌ **DON'T**: Assume suggestions persist between calls
- ❌ **DON'T**: Make blocking/slow operations in `on_suggest()`
- 💡 **Lesson (v1.1.0)**: `on_suggest()` is called frequently - defer heavy work to `on_execute()`

### Items Chain
- ✅ **DO**: Check `items_chain` to understand user navigation state
  ```python
  if len(items_chain) == 1 and self._current_mode == FILTER_MODE:
      self._reset_to_jql_mode()  # User re-invoked keyword
  ```
- ✅ **DO**: Use `items_chain[-1].target()` to detect Tab presses on specific items
- 💡 **Lesson (v1.1.0)**: Items chain helps detect when user re-invokes keyword (reset state)

---

## ⚡ Performance

### API Calls
- ✅ **DO**: Cache API results in instance variables when filtering/searching
- ✅ **DO**: Implement local filtering on cached data
- ❌ **DON'T**: Make API calls on every keystroke in `on_suggest()`
- ❌ **DON'T**: Send incomplete/invalid queries to external APIs
- 💡 **Lesson (v1.1.0)**: Two-phase approach (input → execute → filter) reduced API calls by ~90%

### Blocking Operations
- ✅ **DO**: Execute slow operations (API calls, I/O) in `on_execute()` or background threads
- ✅ **DO**: Use `_execute_jql_query()` pattern: called explicitly, not during typing
- ❌ **DON'T**: Block UI thread in `on_suggest()`
- 💡 **Lesson (v1.1.0)**: Keep on_suggest() non-blocking for responsive UX

### Filtering
- ✅ **DO**: Implement case-insensitive local filtering
  ```python
  filter_lower = filter_text.lower()
  if filter_lower in issue["summary"].lower():
      filtered.append(issue)
  ```
- ✅ **DO**: Search across multiple fields (key, summary, status)
- 💡 **Lesson (v1.1.0)**: Local filtering is instant, no network latency

---

## 🐛 Common Pitfalls

### Keypirinha Behavior
- ⚠️ **Pitfall**: Enter closes Launchbox by default after executing an item
- 🔧 **Solution**: Use Tab for multi-step workflows (keeps Launchbox open)
- 💡 **Lesson (v1.1.0)**: `hit_hint=kp.ItemHitHint.KEEPALL` allows Tab to add item to chain

### Mode Switching
- ⚠️ **Pitfall**: User can re-invoke keyword while in a different mode (e.g., FILTER mode)
- 🔧 **Solution**: Detect re-invocation via `items_chain` length and reset state
  ```python
  if len(items_chain) == 1 and self._current_mode == MODE_FILTER:
      self._reset_to_jql_mode()
  ```
- 💡 **Lesson (v1.1.0)**: Always handle mode resets when keyword is re-invoked

### Invalid User Input
- ⚠️ **Pitfall**: Empty queries or invalid syntax can cause API errors
- 🔧 **Solution**: Validate input before API calls, show hints during typing phase
- 💡 **Lesson (v1.1.0)**: Don't execute queries until user explicitly triggers (Enter/Tab)

### Configuration Changes
- ⚠️ **Pitfall**: Config changes (e.g., keyword) require catalog refresh
- 🔧 **Solution**: Call `on_catalog()` when config changes in `on_events()`
  ```python
  if old_keyword != self._keyword:
      self.on_catalog()
  ```
- 💡 **Lesson (v1.1.0)**: Catalog doesn't auto-update on config change

### INI Config Handling
- ✅ **DO**: Use `settings.has_section()` before iterating
  ```python
  if settings.has_section("jql_shortcuts"):
      for key in settings.keys("jql_shortcuts"):
          value = settings.get_stripped(key, section="jql_shortcuts")
  ```
- ✅ **DO**: INI format supports `=` in values
  ```ini
  me = assignee = currentUser()  # Works fine!
  ```
- 💡 **Lesson (v1.2.0)**: Keypirinha's INI parser handles `=` in values correctly

### Prefix-Based Features
- ✅ **DO**: Use prefix detection for feature gating
  ```python
  if user_input.startswith("#"):
      # Handle shortcuts
      self._handle_shortcut_input(user_input)
  ```
- ✅ **DO**: Case-insensitive matching for better UX
  ```python
  shortcut_name = user_input[1:].lower()  # Remove # and lowercase
  self._jql_shortcuts[key.lower()] = value  # Store lowercase
  ```
- 💡 **Lesson (v1.2.0)**: Prefix patterns enable clean feature separation

### File Path Resolution
- ✅ **DO**: Use `kpu.shell_known_folder_path()` for system paths
  ```python
  config_path = os.path.join(
      kpu.shell_known_folder_path(kpu.FOLDERID.RoamingAppData),
      "Keypirinha",
      "User",
      "keypi_jqe.ini"
  )
  kpu.shell_execute(config_path)  # Opens with default editor
  ```
- 💡 **Lesson (v1.2.0)**: System folders accessible via Keypirinha utils

---

## 📝 Code Patterns

### Item Categories
```python
# Define distinct categories for different item types
ITEMCAT_QUERY = kp.ItemCategory.USER_BASE + 1   # Keyword entry
ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2  # Search results
ITEMCAT_FILTER = kp.ItemCategory.USER_BASE + 3  # Filter mode items
```
💡 Use distinct categories to differentiate item types in `on_execute()`

### Error Handling
```python
try:
    results = self.jira_client.search_issues(jql)
except JiraAuthError as e:
    self.set_suggestions([
        self.create_error_item(
            label="Authentication failed",
            short_desc=str(e)
        )
    ])
except JiraAPIError as e:
    self.err(f"API Error: {str(e)}")
    self.set_suggestions([self.create_error_item(...)])
```
💡 Always show user-friendly errors in suggestions (don't let plugin crash silently)

### Logging
```python
self.dbg(f"[on_suggest] mode={self._current_mode}, input='{user_input[:30]}'")
self.info(f"Executing JQL: {jql[:50]}...")
self.warn("Configuration missing - check keypi_jqe.ini")
self.err(f"[_execute_jql_query] Error: {str(e)}")
```
💡 Use appropriate log levels (dbg/info/warn/err) for debugging and user support

### Mode Management
```python
# State machine pattern
MODE_JQL = "jql"
MODE_FILTER = "filter"

def _reset_to_jql_mode(self):
    """Reset plugin state to JQL mode"""
    self._current_mode = self.MODE_JQL
    self._current_jql = ""
    self._cached_results = []
    self._filter_text = ""
```
💡 Centralized reset method ensures consistent state cleanup

---

## 🎨 UX Patterns

### Visual Feedback
- ✅ **DO**: Show current mode in item labels
  ```python
  label=f"{self._keyword}: {user_input}"           # JQL mode
  label=f"{self._keyword} filter: {filter_text}"   # Filter mode
  ```
- ✅ **DO**: Use descriptive `short_desc` for hints
  ```python
  short_desc="Press Enter to execute query"
  short_desc=f"No results match filter: {filter_text}"
  ```
- 💡 **Lesson (v1.1.0)**: Clear visual feedback helps users understand current state

### Result Formatting
```python
label = f"{issue['key']}: [{issue['status']}] {issue['summary']}"
short_desc = (
    f"Priority: {issue['priority']} | "
    f"Assignee: {issue['assignee']} | "
    f"Created: {issue['created'][:10]}"
)
```
💡 Consistent formatting makes results scannable

### Direct Execution Pattern
- ✅ **DO**: Execute shortcuts directly without showing expansion
  ```python
  # User sees:    #me
  # User doesn't see: assignee = currentUser()
  # Result: Direct execution → better UX
  ```
- ✅ **DO**: Store expanded value in `data_bag` for execution
  ```python
  self.create_item(
      label=f"#{shortcut_name}",
      short_desc=jql_query,  # Show JQL in description
      data_bag=jql_query,    # Store for execution
  )
  ```
- 💡 **Lesson (v1.2.0)**: Hide implementation details for cleaner UX

---

## 🧪 Testing Strategies

### Manual Testing Checklist
- ✅ Test with empty input
- ✅ Test with invalid input (triggers errors)
- ✅ Test with 0 results
- ✅ Test with many results (>50)
- ✅ Test mode switching (JQL → Filter → Reset)
- ✅ Test configuration changes (keyword, credentials)
- ✅ Check logs for API call frequency

### Known Issues to Track
- 🐛 Empty query closes Launchbox (should show error instead)
- 🐛 Old keyword still works after config change (catalog not refreshed)
💡 Document non-critical bugs in BACKLOG.md for future fixes

---

## 🔄 Architecture Patterns

### Two-Phase Workflow
**Pattern**: Separate input phase from execution phase
```
Phase 1: JQL Input Mode
  - User types query
  - NO API calls
  - Show hint: "Press Enter to execute"

Phase 2: Filter Mode
  - Results are cached
  - User types to filter locally
  - NO new API calls
  - Show filtered results
```
💡 **Benefits**: Reduces API calls, faster filtering, better UX

### API Client Separation
- ✅ **DO**: Keep API logic in separate module (`lib/jira_client.py`)
- ✅ **DO**: Use custom exceptions (`JiraAuthError`, `JiraAPIError`, `JiraNetworkError`)
- ❌ **DON'T**: Put API calls directly in plugin class
💡 **Lesson (v1.0.0)**: Clean separation makes testing and error handling easier

---

## 📚 Resources

### Keypirinha Documentation
- **API Reference**: https://keypirinha.com/api.html
- **Plugin Architecture**: https://keypirinha.com/architecture.html
- **Item Hints**: Focus on `ItemArgsHint` and `ItemHitHint` for behavior control

### Common Gotchas
1. **Keypirinha does NOT auto-filter**: Plugin must provide all suggestions
2. **Enter closes Launchbox**: Use Tab for multi-step workflows
3. **Config changes need catalog refresh**: Call `on_catalog()` in `on_events()`
4. **Instance variables persist**: Use them for state, not local variables

---

## 🔧 Development Workflow

### Before Implementation
1. Read this document for relevant patterns
2. Check BACKLOG.md for related features/issues
3. Plan state management upfront (modes, cached data)

### During Implementation
- Use consistent logging (`dbg`, `info`, `warn`, `err`)
- Test frequently in Keypirinha (Ctrl+Alt+R to reload)
- Check logs (F2 in Keypirinha)

### After Implementation
- Add new learnings to this document
- Update relevant sections with new patterns
- Document pitfalls encountered

---

**Version History:**
- **2025-12-22**: v1.2.0 update (JQL Shortcuts - INI handling, prefix detection, file paths)
- **2025-12-20**: Initial version (based on v1.0.0 MVP + v1.1.0 Filter Feature)

---

**Contributing**: Add learnings as you encounter them! Use this format:
```markdown
### New Category
- ✅ **DO**: What worked well
- ❌ **DON'T**: What to avoid
- 💡 **Lesson (vX.X.X)**: Context from specific feature
```
