"""
Unit tests for CQE shortcuts functionality
"""

import unittest


class TestCQLShortcutsParsing(unittest.TestCase):
    """Test CQL shortcuts config parsing"""

    def _parse_shortcuts(self, config_lines):
        """
        Parse shortcuts from config lines (simulates INI parsing)

        Args:
            config_lines: List of "key = value" lines

        Returns:
            Dict of {shortcut_name: cql_query}
        """
        shortcuts = {}
        for line in config_lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if "=" in line:
                # Only split on first = (CQL can contain =)
                key, value = line.split("=", 1)
                key = key.strip().lower()
                value = value.strip()
                if key and value:
                    shortcuts[key] = value
        return shortcuts

    def test_parse_simple_shortcut(self):
        """Test parsing simple shortcut without = in value"""
        config = ["myco = title ~ konzept"]
        result = self._parse_shortcuts(config)

        self.assertEqual(len(result), 1)
        self.assertEqual(result["myco"], "title ~ konzept")

    def test_parse_shortcut_with_equals_in_value(self):
        """Test parsing shortcut with = in CQL value"""
        config = ["me = creator = currentUser()"]
        result = self._parse_shortcuts(config)

        self.assertEqual(len(result), 1)
        self.assertEqual(result["me"], "creator = currentUser()")

    def test_parse_shortcut_multiple_equals(self):
        """Test parsing shortcut with multiple = in CQL value"""
        config = ["complex = type = page and space = MYSPACE"]
        result = self._parse_shortcuts(config)

        self.assertEqual(len(result), 1)
        self.assertEqual(result["complex"], "type = page and space = MYSPACE")

    def test_parse_multiple_shortcuts(self):
        """Test parsing multiple shortcuts"""
        config = [
            "myco = title ~ konzept",
            "mytodo = title ~ todo",
            'recent = lastModified >= now("-7d")',
        ]
        result = self._parse_shortcuts(config)

        self.assertEqual(len(result), 3)
        self.assertIn("myco", result)
        self.assertIn("mytodo", result)
        self.assertIn("recent", result)

    def test_parse_case_insensitive_keys(self):
        """Test that shortcut keys are stored lowercase"""
        config = ["MyShortcut = some query", "UPPERCASE = another query"]
        result = self._parse_shortcuts(config)

        self.assertIn("myshortcut", result)
        self.assertIn("uppercase", result)
        self.assertNotIn("MyShortcut", result)
        self.assertNotIn("UPPERCASE", result)

    def test_parse_ignores_comments(self):
        """Test that comments are ignored"""
        config = [
            "# This is a comment",
            "valid = query here",
            "; Another comment style",
        ]
        result = self._parse_shortcuts(config)

        self.assertEqual(len(result), 1)
        self.assertEqual(result["valid"], "query here")

    def test_parse_ignores_empty_lines(self):
        """Test that empty lines are ignored"""
        config = ["", "valid = query", "   ", "another = query2"]
        result = self._parse_shortcuts(config)

        self.assertEqual(len(result), 2)

    def test_parse_strips_whitespace(self):
        """Test that whitespace is stripped from keys and values"""
        config = ["  mykey  =  my value with spaces  "]
        result = self._parse_shortcuts(config)

        self.assertEqual(result["mykey"], "my value with spaces")

    def test_parse_empty_value_ignored(self):
        """Test that empty values are ignored"""
        config = ["novalue = ", "valid = has value"]
        result = self._parse_shortcuts(config)

        self.assertEqual(len(result), 1)
        self.assertNotIn("novalue", result)


class TestCQLShortcutsMatching(unittest.TestCase):
    """Test CQL shortcuts matching logic"""

    def setUp(self):
        """Set up test shortcuts"""
        self.shortcuts = {
            "myco": "title ~ konzept and creator = currentUser()",
            "mytodo": "title ~ todo and creator = currentUser()",
            "recent": 'lastModified >= now("-7d") ORDER BY lastModified DESC',
            "pages": "type = page",
        }

    def _match_shortcuts(self, shortcuts, user_input):
        """
        Match shortcuts based on user input (prefix matching)

        Args:
            shortcuts: Dict of {name: query}
            user_input: User input after # (e.g., "my" for "#my")

        Returns:
            List of (name, query) tuples that match
        """
        user_input = user_input.lower()
        matches = []

        # Exact match first
        if user_input in shortcuts:
            return [(user_input, shortcuts[user_input])]

        # Prefix matches
        for name, query in sorted(shortcuts.items()):
            if name.startswith(user_input):
                matches.append((name, query))

        return matches

    def test_exact_match(self):
        """Test exact shortcut match"""
        result = self._match_shortcuts(self.shortcuts, "myco")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "myco")

    def test_prefix_match_single(self):
        """Test prefix match with single result"""
        result = self._match_shortcuts(self.shortcuts, "rec")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "recent")

    def test_prefix_match_multiple(self):
        """Test prefix match with multiple results"""
        result = self._match_shortcuts(self.shortcuts, "my")

        self.assertEqual(len(result), 2)
        names = [r[0] for r in result]
        self.assertIn("myco", names)
        self.assertIn("mytodo", names)

    def test_empty_input_returns_all(self):
        """Test empty input returns all shortcuts"""
        result = self._match_shortcuts(self.shortcuts, "")

        self.assertEqual(len(result), 4)

    def test_no_match(self):
        """Test no matching shortcuts"""
        result = self._match_shortcuts(self.shortcuts, "xyz")

        self.assertEqual(len(result), 0)

    def test_case_insensitive_matching(self):
        """Test case-insensitive matching"""
        result_lower = self._match_shortcuts(self.shortcuts, "myco")
        result_upper = self._match_shortcuts(self.shortcuts, "MYCO")
        result_mixed = self._match_shortcuts(self.shortcuts, "MyCo")

        self.assertEqual(len(result_lower), 1)
        self.assertEqual(len(result_upper), 1)
        self.assertEqual(len(result_mixed), 1)

    def test_single_char_prefix(self):
        """Test single character prefix matching"""
        result = self._match_shortcuts(self.shortcuts, "m")

        self.assertEqual(len(result), 2)  # myco, mytodo

    def test_edit_special_shortcut(self):
        """Test that 'edit' prefix doesn't match regular shortcuts"""
        result = self._match_shortcuts(self.shortcuts, "edit")

        self.assertEqual(len(result), 0)  # 'edit' is special, not in shortcuts


class TestCQLShortcutsInputHandling(unittest.TestCase):
    """Test CQL shortcuts input handling (# prefix detection)"""

    def _is_shortcut_input(self, user_input):
        """Check if user input is a shortcut command"""
        return user_input.strip().startswith("#")

    def _extract_shortcut_name(self, user_input):
        """Extract shortcut name from user input"""
        if not self._is_shortcut_input(user_input):
            return None
        return user_input.strip()[1:].lower()  # Remove # and lowercase

    def test_detect_shortcut_input(self):
        """Test detection of shortcut input"""
        self.assertTrue(self._is_shortcut_input("#myco"))
        self.assertTrue(self._is_shortcut_input("#"))
        self.assertTrue(self._is_shortcut_input("  #myco  "))

    def test_detect_non_shortcut_input(self):
        """Test detection of non-shortcut input"""
        self.assertFalse(self._is_shortcut_input("type = page"))
        self.assertFalse(self._is_shortcut_input(""))
        self.assertFalse(self._is_shortcut_input("myco"))

    def test_extract_shortcut_name(self):
        """Test extracting shortcut name from input"""
        self.assertEqual(self._extract_shortcut_name("#myco"), "myco")
        self.assertEqual(self._extract_shortcut_name("#MYCO"), "myco")
        self.assertEqual(self._extract_shortcut_name("#"), "")
        self.assertEqual(self._extract_shortcut_name("  #mytodo  "), "mytodo")

    def test_extract_edit_shortcut(self):
        """Test extracting 'edit' shortcut name"""
        self.assertEqual(self._extract_shortcut_name("#edit"), "edit")
        self.assertEqual(self._extract_shortcut_name("#EDIT"), "edit")

    def test_extract_from_non_shortcut_returns_none(self):
        """Test extracting from non-shortcut returns None"""
        self.assertIsNone(self._extract_shortcut_name("type = page"))
        self.assertIsNone(self._extract_shortcut_name(""))


class TestCQLShortcutsEdgeCases(unittest.TestCase):
    """Test edge cases for CQL shortcuts"""

    def test_shortcut_with_special_chars_in_value(self):
        """Test shortcut values with special characters"""
        shortcuts = {
            "quoted": 'title ~ "my search term"',
            "parens": "creator = currentUser()",
            "brackets": 'label in ("one", "two")',
        }

        self.assertIn("quoted", shortcuts)
        self.assertIn("parens", shortcuts)
        self.assertIn("brackets", shortcuts)

    def test_shortcut_with_order_by(self):
        """Test shortcut with ORDER BY clause"""
        shortcut_value = "type = page ORDER BY lastModified DESC"

        self.assertIn("ORDER BY", shortcut_value)
        self.assertIn("DESC", shortcut_value)

    def test_empty_shortcuts_dict(self):
        """Test handling of empty shortcuts dict"""
        shortcuts = {}

        self.assertEqual(len(shortcuts), 0)
        self.assertNotIn("myco", shortcuts)

    def test_shortcut_name_with_numbers(self):
        """Test shortcut names containing numbers"""
        shortcuts = {"query1": "cql1", "query2": "cql2", "q3": "cql3"}

        self.assertEqual(len(shortcuts), 3)
        self.assertIn("query1", shortcuts)
        self.assertIn("q3", shortcuts)

    def test_shortcut_name_with_underscore(self):
        """Test shortcut names containing underscores"""
        shortcuts = {"my_shortcut": "cql here", "another_one": "more cql"}

        self.assertEqual(len(shortcuts), 2)
        self.assertIn("my_shortcut", shortcuts)


if __name__ == "__main__":
    unittest.main()
