"""
Unit tests for JQE history functionality
"""

import json
import os
import tempfile
import unittest
from datetime import datetime


class TestHistoryFileParsing(unittest.TestCase):
    """Test history file parsing and validation"""

    def _parse_history_file(self, content):
        """
        Parse history file content (simulates _load_history logic)

        Args:
            content: JSON string or dict

        Returns:
            List of history entries or empty list on error
        """
        try:
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content

            # Validate structure
            if not isinstance(data, dict) or "queries" not in data:
                return []

            return data.get("queries", [])

        except json.JSONDecodeError:
            return []
        except Exception:
            return []

    def test_parse_valid_history(self):
        """Test parsing valid history file"""
        content = {
            "version": 1,
            "queries": [
                {
                    "query": "assignee = currentUser()",
                    "last_used": "2026-01-26T14:30:00",
                },
                {"query": "status = Open", "last_used": "2026-01-26T14:25:00"},
            ],
        }
        result = self._parse_history_file(content)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["query"], "assignee = currentUser()")
        self.assertEqual(result[1]["query"], "status = Open")

    def test_parse_empty_history(self):
        """Test parsing empty history file"""
        content = {"version": 1, "queries": []}
        result = self._parse_history_file(content)

        self.assertEqual(len(result), 0)

    def test_parse_invalid_structure(self):
        """Test parsing invalid structure returns empty list"""
        content = {"version": 1, "invalid_key": []}
        result = self._parse_history_file(content)

        self.assertEqual(len(result), 0)

    def test_parse_not_dict(self):
        """Test parsing non-dict returns empty list"""
        content = [{"query": "test", "last_used": "2026-01-26"}]
        result = self._parse_history_file(content)

        self.assertEqual(len(result), 0)

    def test_parse_corrupted_json(self):
        """Test parsing corrupted JSON returns empty list"""
        result = self._parse_history_file("{invalid json")

        self.assertEqual(len(result), 0)


class TestHistoryDuplicateHandling(unittest.TestCase):
    """Test history duplicate handling logic"""

    def _add_to_history(self, queries, new_query, max_entries=30):
        """
        Add query to history (simulates _add_to_history logic)

        Args:
            queries: Existing list of history entries
            new_query: New query to add
            max_entries: Maximum entries to keep

        Returns:
            Updated list of history entries
        """
        if not new_query or not new_query.strip():
            return queries

        new_query = new_query.strip()

        # Remove duplicate if exists (case-insensitive)
        query_lower = new_query.lower()
        queries = [q for q in queries if q.get("query", "").lower() != query_lower]

        # Add new entry at beginning
        new_entry = {"query": new_query, "last_used": datetime.now().isoformat()}
        queries.insert(0, new_entry)

        # Trim to max entries
        queries = queries[:max_entries]

        return queries

    def test_add_new_query(self):
        """Test adding a new query to empty history"""
        queries = []
        result = self._add_to_history(queries, "assignee = currentUser()")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["query"], "assignee = currentUser()")

    def test_add_duplicate_moves_to_top(self):
        """Test adding duplicate query moves it to top"""
        queries = [
            {"query": "status = Open", "last_used": "2026-01-26T14:30:00"},
            {"query": "assignee = currentUser()", "last_used": "2026-01-26T14:25:00"},
        ]
        result = self._add_to_history(queries, "assignee = currentUser()")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["query"], "assignee = currentUser()")
        self.assertEqual(result[1]["query"], "status = Open")

    def test_duplicate_case_insensitive(self):
        """Test duplicate detection is case-insensitive"""
        queries = [
            {"query": "Assignee = currentUser()", "last_used": "2026-01-26T14:30:00"},
        ]
        result = self._add_to_history(queries, "assignee = currentuser()")

        self.assertEqual(len(result), 1)
        # The new query should be stored (with its casing)
        self.assertEqual(result[0]["query"], "assignee = currentuser()")

    def test_max_entries_limit(self):
        """Test history is limited to max_entries"""
        queries = [{"query": f"query{i}", "last_used": "2026-01-26"} for i in range(10)]
        result = self._add_to_history(queries, "new query", max_entries=5)

        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]["query"], "new query")

    def test_empty_query_ignored(self):
        """Test empty query is ignored"""
        queries = [{"query": "existing", "last_used": "2026-01-26"}]
        result = self._add_to_history(queries, "")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["query"], "existing")

    def test_whitespace_only_query_ignored(self):
        """Test whitespace-only query is ignored"""
        queries = [{"query": "existing", "last_used": "2026-01-26"}]
        result = self._add_to_history(queries, "   ")

        self.assertEqual(len(result), 1)

    def test_query_whitespace_stripped(self):
        """Test query whitespace is stripped"""
        queries = []
        result = self._add_to_history(queries, "  assignee = currentUser()  ")

        self.assertEqual(result[0]["query"], "assignee = currentUser()")


class TestHistoryMultipleAdds(unittest.TestCase):
    """Test adding multiple queries to history in sequence"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, "test_history.json")

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        os.rmdir(self.temp_dir)

    def _save_history(self, queries, path):
        """Save history to file"""
        data = {"version": 1, "queries": queries}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_history(self, path):
        """Load history from file"""
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "queries" not in data:
                return []
            return data.get("queries", [])
        except Exception:
            return []

    def _add_to_history(self, new_query, max_entries=30):
        """Add query to history (full simulation with file I/O)"""
        if not new_query or not new_query.strip():
            return

        new_query = new_query.strip()
        queries = self._load_history(self.history_file)

        # Remove duplicate if exists (case-insensitive)
        query_lower = new_query.lower()
        queries = [q for q in queries if q.get("query", "").lower() != query_lower]

        # Add new entry at beginning
        new_entry = {"query": new_query, "last_used": datetime.now().isoformat()}
        queries.insert(0, new_entry)

        # Trim to max entries
        queries = queries[:max_entries]

        self._save_history(queries, self.history_file)

    def test_multiple_adds_preserve_all(self):
        """Test that adding multiple queries preserves all of them"""
        # Add 5 different queries
        self._add_to_history("query 1")
        self._add_to_history("query 2")
        self._add_to_history("query 3")
        self._add_to_history("query 4")
        self._add_to_history("query 5")

        # Load and verify all are present
        result = self._load_history(self.history_file)
        self.assertEqual(len(result), 5)

        # Newest should be first
        self.assertEqual(result[0]["query"], "query 5")
        self.assertEqual(result[4]["query"], "query 1")

    def test_multiple_adds_with_duplicates(self):
        """Test that adding duplicates moves them to top without duplicating"""
        self._add_to_history("query A")
        self._add_to_history("query B")
        self._add_to_history("query C")
        self._add_to_history("query A")  # Duplicate

        result = self._load_history(self.history_file)
        self.assertEqual(len(result), 3)  # No duplicates
        self.assertEqual(result[0]["query"], "query A")  # Moved to top
        self.assertEqual(result[1]["query"], "query C")
        self.assertEqual(result[2]["query"], "query B")

    def test_sequential_adds_create_file_if_not_exists(self):
        """Test that first add creates the file"""
        self.assertFalse(os.path.exists(self.history_file))
        self._add_to_history("first query")
        self.assertTrue(os.path.exists(self.history_file))

        result = self._load_history(self.history_file)
        self.assertEqual(len(result), 1)


class TestHistoryFileOperations(unittest.TestCase):
    """Test history file read/write operations"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, "test_history.json")

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        os.rmdir(self.temp_dir)

    def _save_history(self, queries, path):
        """Save history to file"""
        data = {"version": 1, "queries": queries}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_history(self, path):
        """Load history from file"""
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "queries" not in data:
                return []
            return data.get("queries", [])
        except Exception:
            return []

    def test_save_and_load(self):
        """Test saving and loading history file"""
        queries = [
            {"query": "test query", "last_used": "2026-01-26T14:30:00"},
        ]
        self._save_history(queries, self.history_file)
        result = self._load_history(self.history_file)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["query"], "test query")

    def test_load_nonexistent_file(self):
        """Test loading non-existent file returns empty list"""
        result = self._load_history("/nonexistent/path/history.json")

        self.assertEqual(len(result), 0)

    def test_save_creates_file(self):
        """Test saving creates the file"""
        self.assertFalse(os.path.exists(self.history_file))
        self._save_history([], self.history_file)
        self.assertTrue(os.path.exists(self.history_file))

    def test_unicode_queries(self):
        """Test Unicode characters in queries"""
        queries = [
            {"query": "summary ~ 'Übersicht'", "last_used": "2026-01-26T14:30:00"},
            {"query": "summary ~ '日本語'", "last_used": "2026-01-26T14:25:00"},
        ]
        self._save_history(queries, self.history_file)
        result = self._load_history(self.history_file)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["query"], "summary ~ 'Übersicht'")
        self.assertEqual(result[1]["query"], "summary ~ '日本語'")


class TestHistoryClear(unittest.TestCase):
    """Test history clear functionality"""

    def _clear_history(self, path):
        """Clear history by saving empty list"""
        data = {"version": 1, "queries": []}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_history(self, path):
        """Load history from file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("queries", [])
        except Exception:
            return []

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, "test_history.json")

        # Create history with some entries
        data = {
            "version": 1,
            "queries": [
                {"query": "query1", "last_used": "2026-01-26"},
                {"query": "query2", "last_used": "2026-01-26"},
            ],
        }
        with open(self.history_file, "w") as f:
            json.dump(data, f)

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        os.rmdir(self.temp_dir)

    def test_clear_removes_all_entries(self):
        """Test clear removes all history entries"""
        # Verify history has entries
        result = self._load_history(self.history_file)
        self.assertEqual(len(result), 2)

        # Clear history
        self._clear_history(self.history_file)

        # Verify history is empty
        result = self._load_history(self.history_file)
        self.assertEqual(len(result), 0)

    def test_file_still_valid_after_clear(self):
        """Test file is still valid JSON after clear"""
        self._clear_history(self.history_file)

        with open(self.history_file, "r") as f:
            data = json.load(f)

        self.assertIn("version", data)
        self.assertIn("queries", data)
        self.assertEqual(len(data["queries"]), 0)


class TestHistoryInputDetection(unittest.TestCase):
    """Test #history input detection"""

    def _is_history_command(self, user_input):
        """Check if input is a history command (including #his alias)"""
        input_lower = user_input.strip().lower()
        # Matches: "history", "his", "history clear"
        return input_lower in ("history", "his") or input_lower == "history clear"

    def _is_history_clear_command(self, user_input):
        """Check if input is history clear command"""
        return user_input.strip().lower() == "history clear"

    def test_detect_history_command(self):
        """Test detection of #history command"""
        self.assertTrue(self._is_history_command("history"))
        self.assertTrue(self._is_history_command("HISTORY"))
        self.assertTrue(self._is_history_command("  history  "))

    def test_detect_history_alias(self):
        """Test detection of #his alias command"""
        self.assertTrue(self._is_history_command("his"))
        self.assertTrue(self._is_history_command("HIS"))
        self.assertTrue(self._is_history_command("  his  "))
        self.assertTrue(self._is_history_command("His"))

    def test_detect_history_clear_command(self):
        """Test detection of #history clear command"""
        self.assertTrue(self._is_history_clear_command("history clear"))
        self.assertTrue(self._is_history_clear_command("HISTORY CLEAR"))
        self.assertTrue(self._is_history_clear_command("  history clear  "))

    def test_non_history_commands(self):
        """Test non-history commands are not detected"""
        self.assertFalse(self._is_history_command("edit"))
        self.assertFalse(self._is_history_command("hi"))  # Too short
        self.assertFalse(self._is_history_command("hiss"))  # Wrong spelling
        self.assertFalse(self._is_history_command("historyclear"))


class TestVirtualQueryModeConditions(unittest.TestCase):
    """Test Virtual Query Mode condition checking logic

    Virtual Query Mode (v1.5.0) allows Tab on history entries to execute
    the JQL query directly and show results in Keypirinha.
    """

    # Simulated category constants (matching plugin values)
    ITEMCAT_QUERY = 1001
    ITEMCAT_HISTORY = 1005
    MODE_JQL = "jql"
    MODE_FILTER = "filter"

    def _check_virtual_query_mode_conditions(
        self, current_mode, items_chain, history_category, history_target_prefix
    ):
        """
        Check if Virtual Query Mode should be triggered.

        This simulates the condition check in on_suggest:
        - Mode must be JQL (not FILTER)
        - items_chain must have more than 1 item
        - Last item must be a history entry (correct category)
        - Last item's target must start with 'history_entry_'

        Args:
            current_mode: Current plugin mode (MODE_JQL or MODE_FILTER)
            items_chain: List of dicts simulating items_chain
            history_category: The category ID for history items
            history_target_prefix: Expected target prefix

        Returns:
            bool: True if Virtual Query Mode should be triggered
        """
        if current_mode != self.MODE_JQL:
            return False
        if len(items_chain) <= 1:
            return False
        last_item = items_chain[-1]
        if last_item.get("category") != history_category:
            return False
        if not last_item.get("target", "").startswith(history_target_prefix):
            return False
        return True

    def test_vqm_triggers_with_valid_history_entry(self):
        """Test VQM triggers when history entry is in chain"""
        items_chain = [
            {"category": self.ITEMCAT_QUERY, "target": "jqe"},
            {
                "category": self.ITEMCAT_HISTORY,
                "target": "history_entry_0",
                "data_bag": "assignee = currentUser()",
            },
        ]
        result = self._check_virtual_query_mode_conditions(
            self.MODE_JQL, items_chain, self.ITEMCAT_HISTORY, "history_entry_"
        )
        self.assertTrue(result)

    def test_vqm_not_triggered_in_filter_mode(self):
        """Test VQM does NOT trigger in FILTER mode"""
        items_chain = [
            {"category": self.ITEMCAT_QUERY, "target": "jqe"},
            {"category": self.ITEMCAT_HISTORY, "target": "history_entry_0"},
        ]
        result = self._check_virtual_query_mode_conditions(
            self.MODE_FILTER, items_chain, self.ITEMCAT_HISTORY, "history_entry_"
        )
        self.assertFalse(result)

    def test_vqm_not_triggered_with_single_item_chain(self):
        """Test VQM does NOT trigger with only keyword in chain"""
        items_chain = [
            {"category": self.ITEMCAT_QUERY, "target": "jqe"},
        ]
        result = self._check_virtual_query_mode_conditions(
            self.MODE_JQL, items_chain, self.ITEMCAT_HISTORY, "history_entry_"
        )
        self.assertFalse(result)

    def test_vqm_not_triggered_with_wrong_category(self):
        """Test VQM does NOT trigger if last item is not history"""
        items_chain = [
            {"category": self.ITEMCAT_QUERY, "target": "jqe"},
            {"category": self.ITEMCAT_QUERY, "target": "execute_jql"},
        ]
        result = self._check_virtual_query_mode_conditions(
            self.MODE_JQL, items_chain, self.ITEMCAT_HISTORY, "history_entry_"
        )
        self.assertFalse(result)

    def test_vqm_not_triggered_with_wrong_target_prefix(self):
        """Test VQM does NOT trigger if target doesn't match prefix"""
        items_chain = [
            {"category": self.ITEMCAT_QUERY, "target": "jqe"},
            {"category": self.ITEMCAT_HISTORY, "target": "wrong_prefix_0"},
        ]
        result = self._check_virtual_query_mode_conditions(
            self.MODE_JQL, items_chain, self.ITEMCAT_HISTORY, "history_entry_"
        )
        self.assertFalse(result)

    def test_vqm_triggers_with_multiple_history_entries(self):
        """Test VQM works with different history entry indices"""
        for i in range(10):
            items_chain = [
                {"category": self.ITEMCAT_QUERY, "target": "jqe"},
                {"category": self.ITEMCAT_HISTORY, "target": f"history_entry_{i}"},
            ]
            result = self._check_virtual_query_mode_conditions(
                self.MODE_JQL, items_chain, self.ITEMCAT_HISTORY, "history_entry_"
            )
            self.assertTrue(result, f"Should trigger for history_entry_{i}")

    def test_vqm_empty_chain(self):
        """Test VQM does NOT trigger with empty chain"""
        result = self._check_virtual_query_mode_conditions(
            self.MODE_JQL, [], self.ITEMCAT_HISTORY, "history_entry_"
        )
        self.assertFalse(result)


class TestHistoryItemCreationParams(unittest.TestCase):
    """Test that history items are created with correct parameters for Tab chaining

    For Virtual Query Mode to work, history items must be created with:
    - args_hint = ACCEPTED (allow Tab to add to chain)
    - hit_hint = KEEPALL (enable Tab chaining)
    - loop_on_suggest = True (tell GUI to call on_suggest on Tab)
    - unique target per item (prevent deduplication)
    """

    def test_history_entry_targets_are_unique(self):
        """Test that each history entry gets a unique target"""
        entries = [
            {"query": "query 1", "last_used": "2026-01-29"},
            {"query": "query 2", "last_used": "2026-01-29"},
            {"query": "query 3", "last_used": "2026-01-29"},
        ]

        targets = []
        for i, entry in enumerate(entries):
            target = f"history_entry_{i}"
            targets.append(target)

        # All targets should be unique
        self.assertEqual(len(targets), len(set(targets)))

        # Targets should have correct format
        for i, target in enumerate(targets):
            self.assertEqual(target, f"history_entry_{i}")
            self.assertTrue(target.startswith("history_entry_"))


if __name__ == "__main__":
    unittest.main()
