"""
Unit tests for User Search filter logic
"""

import unittest


class TestUSFilterLogic(unittest.TestCase):
    """Test filter functionality for User Search plugin"""

    def _filter_results(self, cached_results, filter_text):
        """
        Filter cached results based on filter text
        (Copy of the implementation from keypi_us/__init__.py for testing)

        Args:
            cached_results: List of cached user results
            filter_text: Text to filter by (case-insensitive)

        Returns:
            List of filtered users
        """
        if not cached_results:
            return []

        filter_lower = filter_text.lower()
        filtered = []

        for user in cached_results:
            # Search in: display_name, email
            searchable_text = " ".join(
                [
                    user.get("display_name", ""),
                    user.get("email", "") or "",
                ]
            ).lower()

            if filter_lower in searchable_text:
                filtered.append(user)

        return filtered

    def setUp(self):
        """Set up test data"""
        self.test_users = [
            {
                "account_id": "1",
                "display_name": "Max Mustermann",
                "email": "max.mustermann@company.com",
                "active": True,
                "account_type": "atlassian",
            },
            {
                "account_id": "2",
                "display_name": "Anna Schmidt",
                "email": "anna.schmidt@company.com",
                "active": True,
                "account_type": "atlassian",
            },
            {
                "account_id": "3",
                "display_name": "John Doe",
                "email": None,  # No email available
                "active": True,
                "account_type": "atlassian",
            },
            {
                "account_id": "4",
                "display_name": "Service Bot",
                "email": "bot@company.com",
                "active": True,
                "account_type": "app",
            },
            {
                "account_id": "5",
                "display_name": "Max Schmidt",
                "email": "max.schmidt@other.com",
                "active": False,
                "account_type": "atlassian",
            },
        ]

    def test_filter_by_display_name(self):
        """Test filtering by display name"""
        result = self._filter_results(self.test_users, "max")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["display_name"], "Max Mustermann")
        self.assertEqual(result[1]["display_name"], "Max Schmidt")

    def test_filter_by_email(self):
        """Test filtering by email address"""
        result = self._filter_results(self.test_users, "schmidt@company")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["display_name"], "Anna Schmidt")

    def test_filter_by_email_domain(self):
        """Test filtering by email domain"""
        result = self._filter_results(self.test_users, "@company.com")

        self.assertEqual(len(result), 3)

    def test_filter_case_insensitive(self):
        """Test case-insensitive filtering"""
        result_lower = self._filter_results(self.test_users, "anna")
        result_upper = self._filter_results(self.test_users, "ANNA")
        result_mixed = self._filter_results(self.test_users, "AnNa")

        self.assertEqual(len(result_lower), 1)
        self.assertEqual(len(result_upper), 1)
        self.assertEqual(len(result_mixed), 1)
        self.assertEqual(result_lower[0]["account_id"], result_upper[0]["account_id"])

    def test_filter_no_matches(self):
        """Test filtering with no matches"""
        result = self._filter_results(self.test_users, "nonexistent")

        self.assertEqual(len(result), 0)

    def test_filter_empty_string(self):
        """Test filtering with empty string (should match all)"""
        result = self._filter_results(self.test_users, "")

        self.assertEqual(len(result), 5)

    def test_filter_partial_match(self):
        """Test filtering with partial match"""
        result = self._filter_results(self.test_users, "muster")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["display_name"], "Max Mustermann")

    def test_filter_empty_cached_results(self):
        """Test filtering with empty cached results"""
        result = self._filter_results([], "max")

        self.assertEqual(len(result), 0)

    def test_filter_user_without_email(self):
        """Test filtering finds users without email by name"""
        result = self._filter_results(self.test_users, "john")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["display_name"], "John Doe")
        self.assertIsNone(result[0]["email"])

    def test_filter_excludes_user_without_email_on_email_search(self):
        """Test filtering by email excludes users with no email"""
        result = self._filter_results(self.test_users, "@")

        # Should find 4 users (all with emails)
        self.assertEqual(len(result), 4)
        for user in result:
            self.assertIsNotNone(user["email"])


if __name__ == "__main__":
    unittest.main()
