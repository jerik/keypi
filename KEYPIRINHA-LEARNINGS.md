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

## 🎭 Multi-Action Pattern

### The Correct Way: set_actions()
- ✅ **DO**: Use `set_actions()` in `on_start()` to register actions for item categories
  ```python
  def on_start(self):
      self.set_actions(
          self.ITEMCAT_RESULT,
          [
              self.create_action(name="open", label="Open page"),
              self.create_action(name="copy_url", label="Copy URL"),
              self.create_action(name="edit", label="Edit page"),
          ],
      )
  ```
- ✅ **DO**: Use `hit_hint=IGNORE` and `args_hint=FORBIDDEN` for actionable items
  ```python
  self.create_item(
      category=ITEMCAT_RESULT,
      hit_hint=kp.ItemHitHint.IGNORE,      # Standard hint
      args_hint=kp.ItemArgsHint.FORBIDDEN,  # No additional args
  )
  ```
- ❌ **DON'T**: Use items_chain detection + KEEPALL pattern (doesn't work reliably)
- 💡 **Lesson (CQE v1.1.0)**: set_actions() is the official Keypirinha way - see chrome-history plugin

### Handling Actions in on_execute()
- ✅ **DO**: Check if action parameter is None (default action) or has specific name
  ```python
  def on_execute(self, item, action):
      if item.category() == ITEMCAT_RESULT:
          if not action:
              # Default action (Enter pressed)
              kpu.shell_execute(item.target())
          elif action.name() == "copy_url":
              # Tab -> Select action
              kpu.set_clipboard(item.target())
          elif action.name() == "edit":
              # Custom action
              edit_url = self._generate_edit_url(item.target())
              kpu.shell_execute(edit_url)
  ```
- ✅ **DO**: Store full item data in `data_bag` as JSON for complex items
  ```python
  data_bag=json.dumps({"id": page_id, "url": page_url, "title": title})
  ```
- 💡 **Lesson (CQE v1.1.0)**: action parameter can be None - always check!

### Action Best Practices
- ✅ **DO**: Provide clear, descriptive action labels
  ```python
  self.create_action(name="open", label="Open page", short_desc="Open page in browser")
  ```
- ✅ **DO**: Keep action names simple (lowercase, underscore-separated)
- ✅ **DO**: First action is default (shown when user presses Enter without Tab)
- 💡 **Lesson (CQE v1.1.0)**: Action order matters - most common action first

### Clipboard Integration
- ✅ **DO**: Use `kpu.set_clipboard()` for copy operations
  ```python
  kpu.set_clipboard(url)  # Copy URL to clipboard
  ```
- ✅ **DO**: Consider NOT resetting mode after clipboard operations (user might copy multiple)
  ```python
  elif action.name() == "copy_url":
      kpu.set_clipboard(url)
      # Don't reset - user might want to copy multiple URLs
  ```
- 💡 **Lesson (CQE v1.1.0)**: Clipboard actions benefit from keeping Launchbox open

---

## 🔗 URL Transformations

### Regex Patterns for URL Manipulation
- ✅ **DO**: Use regex to extract URL components for transformations
  ```python
  import re
  match = re.match(r"(.*?/wiki/spaces/[^/]+)/pages/\d+", page_url)
  if match:
      base_path = match.group(1)
      edit_url = f"{base_path}/pages/edit-v2/{page_id}"
  ```
- ✅ **DO**: Provide fallback behavior for malformed URLs
  ```python
  else:
      self.warn(f"Could not parse URL: {page_url}")
      return page_url  # Fallback to original
  ```
- 💡 **Lesson (CQE v1.1.0)**: URL transformations need robust regex + fallback

### Edit Mode URLs
- ✅ **DO**: Transform view URLs to edit URLs using consistent patterns
  - View: `<base>/wiki/spaces/FOO/pages/123456/title`
  - Edit: `<base>/wiki/spaces/FOO/pages/edit-v2/123456`
- ✅ **DO**: Use page ID from API response, not from URL (they might differ)
- 💡 **Lesson (CQE v1.1.0)**: Confluence edit URLs follow `/pages/edit-v2/{id}` pattern

---

## 📊 Data Handling

### API Expand Parameters
- ✅ **DO**: Use `expand` parameter to request full nested objects from API
  ```python
  params = {
      "cql": cql_query,
      "expand": "space,version",  # Request full space and version data
  }
  ```
- ⚠️ **Pitfall**: Without expand, Confluence API returns empty objects `space={}`, `version={}`
- ✅ **DO**: Check API documentation for available expand options
- 💡 **Lesson (CQE v1.1.0)**: Always use expand for nested data - saves debugging time!

### Parsing API Responses
- ✅ **DO**: Extract date fields and format them consistently
  ```python
  last_modified = version.get("when", "")
  if last_modified:
      last_modified_date = last_modified.split("T")[0]  # 2026-01-21
  ```
- ✅ **DO**: Provide fallback values for missing fields
  ```python
  last_mod = item.get('last_modified', 'N/A')
  ```
- ✅ **DO**: Log sample API responses during debugging to verify data structure
  ```python
  self.dbg(f"[API Sample] space={sample.get('space')}, version={sample.get('version')}")
  ```
- 💡 **Lesson (CQE v1.1.0)**: Date formatting should be ISO-8601 (YYYY-MM-DD) for consistency

### JSON in data_bag
- ✅ **DO**: Store complex objects as JSON in `data_bag`
  ```python
  import json
  data_bag=json.dumps(item)  # Store entire item
  item_data = json.loads(result_item.data_bag())  # Retrieve
  ```
- ✅ **DO**: Document what data is stored in `data_bag` for each item type
- 💡 **Lesson (CQE v1.1.0)**: JSON serialization enables rich data passing between suggest/execute

---

## 🧪 Testing Strategies

### Unit Test Structure
- ✅ **DO**: Create separate test files for different components
  ```
  tests/
    __init__.py
    test_confluence_client.py  # API client tests
    test_url_transformations.py  # URL manipulation tests
  ```
- ✅ **DO**: Test edge cases: missing fields, malformed data, empty responses
- ✅ **DO**: Test URL transformations with various formats (encoded, plus signs, etc.)
- 💡 **Lesson (CQE v1.1.0)**: Comprehensive tests catch API response variations

### Test Coverage
- ✅ **DO**: Test date parsing with different formats
- ✅ **DO**: Test URL transformations with edge cases (short/long space keys, special chars)
- ✅ **DO**: Test fallback behavior for malformed inputs
- 💡 **Lesson (CQE v1.1.0)**: Test both happy path and error cases

---

## 🚫 API Limitations (Critical Knowledge)

### set_suggestions() Does NOT Work in on_execute()
- ⚠️ **Critical**: `set_suggestions()` calls in `on_execute()` are **completely ignored**
- 📝 **Reason**: Keypirinha closes the Launchbox immediately after `on_execute()` returns
- 🔧 **Workaround Options**:
  1. Use **actions** (`set_actions()`) to provide alternative behaviors
  2. Use **clipboard** to pass data to user
  3. Open **external URLs** (browser, apps)
- 💡 **Lesson (JQE v1.4.0)**: Don't try to show new suggestions after Enter - use actions instead!

### No Input Manipulation
- ⚠️ **Critical**: There is **NO API** to programmatically set or modify user input
- ⚠️ **Critical**: There is **NO API** to keep the Launchbox open after `on_execute()`
- 📝 **Architecture**: Plugins react to user input; they cannot initiate input changes
- 💡 **Lesson (JQE v1.4.0)**: Accept this limitation and design UX around it

### Tab Key Behavior
- ⚠️ **Pitfall**: Tab behavior depends on `args_hint`:
  - `ACCEPTED`: Tab adds item to items_chain → triggers `on_suggest()`
  - `FORBIDDEN`: Tab behaves like Enter → triggers `on_execute()`
- ⚠️ **Pitfall**: Tab only works reliably at the **start** of item selection
- 💡 **Lesson (JQE v1.4.0)**: Don't rely on Tab for complex multi-step workflows

### Item Deduplication
- ⚠️ **Pitfall**: Keypirinha **deduplicates items with the same `target`**
- 🔧 **Solution**: Use unique targets for each item (e.g., `target=f"history_entry_{i}"`)
- 💡 **Lesson (JQE v1.4.0)**: Always use unique targets when showing lists of items

---

## 🔗 Jira URL Patterns

### JQL Search URL
- ✅ **DO**: Use URL format `<jira_url>/issues/?jql=<encoded_jql>` for browser search
  ```python
  from urllib.parse import quote
  encoded_jql = quote(jql_query, safe="")
  search_url = f"{self.jira_url}/issues/?jql={encoded_jql}"
  ```
- ✅ **DO**: URL-encode the JQL query (spaces, special chars)
- 💡 **Lesson (JQE v1.4.0)**: Direct browser URLs are useful when set_suggestions() doesn't work

---

**Version History:**
- **2026-01-27**: JQE v1.4.0 update (History actions, API limitations documentation)
- **2026-01-26**: JQE v1.4.0 update (Query History - JSON file storage, persistent state)
- **2026-01-26**: CQE v1.2.0 update (CQL Shortcuts - same pattern as JQL Shortcuts)
- **2026-01-22**: CQE v1.1.0 update (Multi-actions, URL transformations, lastModified field, unit tests)
- **2025-12-22**: JQE v1.2.0 update (JQL Shortcuts - INI handling, prefix detection, file paths)
- **2025-12-20**: Initial version (based on JQE v1.0.0 MVP + v1.1.0 Filter Feature)

---

**Contributing**: Add learnings as you encounter them! Use this format:
```markdown
### New Category
- ✅ **DO**: What worked well
- ❌ **DON'T**: What to avoid
- 💡 **Lesson (vX.X.X)**: Context from specific feature
```
