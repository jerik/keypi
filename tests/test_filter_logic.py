"""
Unit tests for filter logic
"""

import unittest


class TestFilterLogic(unittest.TestCase):
    """Test filter functionality"""

    def _filter_results(self, cached_results, filter_text):
        """
        Filter cached results based on filter text
        (Copy of the implementation from __init__.py for testing)

        Args:
            cached_results: List of cached results
            filter_text: Text to filter by (case-insensitive)

        Returns:
            List of filtered content items
        """
        if not cached_results:
            return []

        filter_lower = filter_text.lower()
        filtered = []

        for item in cached_results:
            # Search in: Title, Space Name, Type
            searchable_text = " ".join(
                [
                    item.get("title", ""),
                    item.get("space_name", ""),
                    item.get("type", ""),
                ]
            ).lower()

            if filter_lower in searchable_text:
                filtered.append(item)

        return filtered

    def setUp(self):
        """Set up test data"""
        self.test_results = [
            {
                "id": "1",
                "title": "Setup Guide",
                "space_name": "Documentation",
                "type": "page",
            },
            {
                "id": "2",
                "title": "API Reference",
                "space_name": "Development",
                "type": "page",
            },
            {
                "id": "3",
                "title": "Meeting Notes",
                "space_name": "Documentation",
                "type": "blogpost",
            },
            {
                "id": "4",
                "title": "Setup Instructions",
                "space_name": "Operations",
                "type": "page",
            },
        ]

    def test_filter_by_title(self):
        """Test filtering by title"""
        result = self._filter_results(self.test_results, "setup")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Setup Guide")
        self.assertEqual(result[1]["title"], "Setup Instructions")

    def test_filter_by_space(self):
        """Test filtering by space name"""
        result = self._filter_results(self.test_results, "documentation")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["space_name"], "Documentation")
        self.assertEqual(result[1]["space_name"], "Documentation")

    def test_filter_by_type(self):
        """Test filtering by content type"""
        result = self._filter_results(self.test_results, "blogpost")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "blogpost")

    def test_filter_case_insensitive(self):
        """Test case-insensitive filtering"""
        result_lower = self._filter_results(self.test_results, "api")
        result_upper = self._filter_results(self.test_results, "API")
        result_mixed = self._filter_results(self.test_results, "Api")

        self.assertEqual(len(result_lower), 1)
        self.assertEqual(len(result_upper), 1)
        self.assertEqual(len(result_mixed), 1)
        self.assertEqual(result_lower[0]["id"], result_upper[0]["id"])

    def test_filter_no_matches(self):
        """Test filtering with no matches"""
        result = self._filter_results(self.test_results, "nonexistent")

        self.assertEqual(len(result), 0)

    def test_filter_empty_string(self):
        """Test filtering with empty string (should match all)"""
        result = self._filter_results(self.test_results, "")

        self.assertEqual(len(result), 4)

    def test_filter_partial_match(self):
        """Test filtering with partial match"""
        result = self._filter_results(self.test_results, "oper")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["space_name"], "Operations")

    def test_filter_empty_cached_results(self):
        """Test filtering with empty cached results"""
        result = self._filter_results([], "setup")

        self.assertEqual(len(result), 0)

    def test_filter_with_missing_fields(self):
        """Test filtering when items have missing fields"""
        incomplete_results = [
            {"id": "1", "title": "Test Page"},  # Missing space_name and type
            {"id": "2", "space_name": "TestSpace"},  # Missing title and type
        ]

        result = self._filter_results(incomplete_results, "test")

        self.assertEqual(len(result), 2)

    def test_filter_multiple_words_in_title(self):
        """Test filtering matches across multiple fields"""
        result = self._filter_results(self.test_results, "api")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "API Reference")


if __name__ == "__main__":
    unittest.main()
