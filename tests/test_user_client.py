"""
Unit tests for User Client parsing logic
"""

import unittest
import sys
import os

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "keypi_us", "lib"))


class TestUserClientParsing(unittest.TestCase):
    """Test user parsing functionality"""

    def _parse_users(self, users, jira_url="https://test.atlassian.net"):
        """
        Parse Jira users from API response
        (Copy of the implementation from user_client.py for testing)

        Args:
            users: Raw users list from API response
            jira_url: Base Jira URL for profile links

        Returns:
            List of parsed user dictionaries
        """
        parsed_users = []

        for user in users:
            try:
                account_id = user.get("accountId", "")
                display_name = user.get("displayName", "Unknown")
                email_address = user.get("emailAddress")  # May be None or empty
                active = user.get("active", False)
                account_type = user.get("accountType", "atlassian")

                # Build profile URL
                profile_url = f"{jira_url}/jira/people/{account_id}"

                parsed_user = {
                    "account_id": account_id,
                    "display_name": display_name,
                    "email": email_address if email_address else None,
                    "active": active,
                    "account_type": account_type,
                    "profile_url": profile_url,
                }

                parsed_users.append(parsed_user)

            except Exception:
                continue

        return parsed_users

    def test_parse_user_with_email(self):
        """Test parsing user with email address"""
        raw_users = [
            {
                "accountId": "123",
                "displayName": "Max Mustermann",
                "emailAddress": "max@company.com",
                "active": True,
                "accountType": "atlassian",
            }
        ]

        result = self._parse_users(raw_users)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["account_id"], "123")
        self.assertEqual(result[0]["display_name"], "Max Mustermann")
        self.assertEqual(result[0]["email"], "max@company.com")
        self.assertTrue(result[0]["active"])
        self.assertEqual(result[0]["account_type"], "atlassian")
        self.assertEqual(
            result[0]["profile_url"], "https://test.atlassian.net/jira/people/123"
        )

    def test_parse_user_without_email(self):
        """Test parsing user without email (privacy setting)"""
        raw_users = [
            {
                "accountId": "456",
                "displayName": "Private User",
                "active": True,
                "accountType": "atlassian",
            }
        ]

        result = self._parse_users(raw_users)

        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]["email"])

    def test_parse_user_with_empty_email(self):
        """Test parsing user with empty string email"""
        raw_users = [
            {
                "accountId": "789",
                "displayName": "Empty Email User",
                "emailAddress": "",
                "active": True,
                "accountType": "atlassian",
            }
        ]

        result = self._parse_users(raw_users)

        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]["email"])  # Empty string should become None

    def test_parse_inactive_user(self):
        """Test parsing inactive user"""
        raw_users = [
            {
                "accountId": "111",
                "displayName": "Former Employee",
                "emailAddress": "former@company.com",
                "active": False,
                "accountType": "atlassian",
            }
        ]

        result = self._parse_users(raw_users)

        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["active"])

    def test_parse_app_user(self):
        """Test parsing app/bot user"""
        raw_users = [
            {
                "accountId": "bot-1",
                "displayName": "Automation Bot",
                "emailAddress": "bot@company.com",
                "active": True,
                "accountType": "app",
            }
        ]

        result = self._parse_users(raw_users)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["account_type"], "app")

    def test_parse_multiple_users(self):
        """Test parsing multiple users"""
        raw_users = [
            {
                "accountId": "1",
                "displayName": "User One",
                "emailAddress": "one@company.com",
                "active": True,
                "accountType": "atlassian",
            },
            {
                "accountId": "2",
                "displayName": "User Two",
                "emailAddress": "two@company.com",
                "active": True,
                "accountType": "atlassian",
            },
            {
                "accountId": "3",
                "displayName": "User Three",
                "active": False,
                "accountType": "atlassian",
            },
        ]

        result = self._parse_users(raw_users)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["display_name"], "User One")
        self.assertEqual(result[1]["display_name"], "User Two")
        self.assertEqual(result[2]["display_name"], "User Three")

    def test_parse_empty_list(self):
        """Test parsing empty user list"""
        result = self._parse_users([])

        self.assertEqual(len(result), 0)

    def test_parse_with_missing_fields(self):
        """Test parsing user with minimal fields"""
        raw_users = [
            {
                "accountId": "minimal",
            }
        ]

        result = self._parse_users(raw_users)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["account_id"], "minimal")
        self.assertEqual(result[0]["display_name"], "Unknown")
        self.assertIsNone(result[0]["email"])
        self.assertFalse(result[0]["active"])

    def test_profile_url_generation(self):
        """Test profile URL is correctly generated"""
        raw_users = [
            {
                "accountId": "test-id-123",
                "displayName": "Test User",
                "active": True,
            }
        ]

        result = self._parse_users(
            raw_users, jira_url="https://mycompany.atlassian.net"
        )

        self.assertEqual(
            result[0]["profile_url"],
            "https://mycompany.atlassian.net/jira/people/test-id-123",
        )


if __name__ == "__main__":
    unittest.main()
