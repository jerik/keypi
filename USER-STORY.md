# better jqe history feaure

You are an expert Keypirinha plugin developer (Python) and you know the Keypirinha Plugin API.

Goal
Implement “History → Virtual Query Mode” for my Keypirinha plugin `jqe` (jira-query-plugin). Today, `#history` shows previous JQL queries and pressing Enter on a history entry copies the JQL to clipboard. I want a smoother flow:

Desired UX
1) User opens Keypirinha
2) types `jqe` and presses Enter (enters plugin / query-mode)
3) types `#history` and presses Enter (enters history-mode)
4) history entries (previous JQLs) are shown and filterable
5) user selects a history entry and presses Enter
6) instead of copying to clipboard and closing, the plugin switches into a “virtual query results mode”:
   - the selected history JQL is stored internally
   - the plugin immediately shows the Jira issues resulting from that JQL as suggestions
   - user can type to filter those issue results
   - pressing Enter on an issue executes the default action (same as the normal jql-query-feature)
Optional: provide a secondary action on history entries that still copies the JQL to clipboard.

Hard constraints (Keypirinha API)
- Do NOT try to programmatically set the launcher input/query text; Keypirinha does not allow that.
- Do NOT try to “re-enter” the plugin by injecting input. Use internal plugin state instead.
- Keep Keypirinha’s normal filtering behavior: show suggestions; allow user typing to filter.

Implementation requirements
- Add an explicit internal state machine to the plugin, e.g. modes: `query`, `history`, `results`.
- Use `on_suggest(user_input, items_chain)` to route behavior based on the current mode and/or items_chain.
- When `#history` is selected, show history entries as suggestions (existing behavior).
- When a history entry is executed, do NOT close the flow. Switch to results mode and show JQL results immediately.
  - Use `loop_on_suggest=True` on the history items (or the correct step item) so that selecting them leads back into `on_suggest` with an updated items_chain.
  - Store the selected JQL in plugin state (e.g. `self.pending_jql`).
  - Then fetch Jira issues for that JQL and return them as suggestions.
- Reuse existing code paths for executing a JQL and for rendering issue items (to match the normal jql-query-feature).
- Ensure user can type to filter issue items; do not implement custom filtering unless necessary.
- Ensure default action on issue item remains unchanged.
- Add a “Back” item (optional) that returns to history-mode or query-mode.
- Keep persistence for history unchanged (whatever storage is used now).

Deliverables
1) Identify and modify the relevant plugin file(s) in my repo (jqe plugin).
2) Provide a clean patch or code diff.
3) Explain briefly how the state machine works and how `loop_on_suggest` + `items_chain` are used to keep the UI open.

Repo context
The plugin lives in my repository: https://github.com/jerik/keypi
Locate the `jqe` plugin folder and implement changes there.

Quality bar
- Minimal, readable changes.
- No breaking changes to the standard jql-query-feature.
- Preserve existing shortcut-feature and history storage.
- Add small comments where mode transitions happen.

Now implement it.
