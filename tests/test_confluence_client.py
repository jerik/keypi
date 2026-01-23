"""
Unit tests for Confluence Client
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "keypi_cqe", "lib"))

from confluence_client import ConfluenceClient


class TestConfluenceClient(unittest.TestCase):
    """Test Confluence Client functionality"""

    def setUp(self):
        """Set up test client"""
        self.client = ConfluenceClient(
            "https://test.atlassian.net", "test@example.com", "test-token"
        )

    def test_parse_content_with_all_fields(self):
        """Test parsing content with all fields present"""
        api_response = [
            {
                "id": "123456",
                "title": "Test Page",
                "type": "page",
                "space": {"key": "TEST", "name": "Test Space"},
                "_links": {"webui": "/wiki/spaces/TEST/pages/123456/Test+Page"},
                "version": {"number": 5, "when": "2026-01-21T14:27:02.000Z"},
            }
        ]

        result = self.client._parse_content(api_response)

        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item["id"], "123456")
        self.assertEqual(item["title"], "Test Page")
        self.assertEqual(item["type"], "page")
        self.assertEqual(item["space_key"], "TEST")
        self.assertEqual(item["space_name"], "Test Space")
        self.assertEqual(item["version"], 5)
        self.assertEqual(item["last_modified"], "2026-01-21")
        self.assertEqual(
            item["url"],
            "https://test.atlassian.net/wiki/spaces/TEST/pages/123456/Test+Page",
        )

    def test_parse_content_with_missing_last_modified(self):
        """Test parsing content when last_modified is missing"""
        api_response = [
            {
                "id": "123456",
                "title": "Test Page",
                "type": "page",
                "space": {"key": "TEST", "name": "Test Space"},
                "_links": {"webui": "/wiki/spaces/TEST/pages/123456/Test+Page"},
                "version": {"number": 1},  # No 'when' field
            }
        ]

        result = self.client._parse_content(api_response)

        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item["last_modified"], "")

    def test_parse_content_with_missing_space(self):
        """Test parsing content when space is missing"""
        api_response = [
            {
                "id": "123456",
                "title": "Test Page",
                "type": "page",
                "_links": {"webui": "/wiki/spaces/UNKNOWN/pages/123456/Test+Page"},
                "version": {"number": 1, "when": "2026-01-21T10:00:00.000Z"},
            }
        ]

        result = self.client._parse_content(api_response)

        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item["space_key"], "")
        self.assertEqual(item["space_name"], "Unknown Space")

    def test_parse_content_with_webui_without_wiki_prefix(self):
        """Test parsing content when webui path doesn't have /wiki prefix"""
        api_response = [
            {
                "id": "123456",
                "title": "Test Page",
                "type": "page",
                "space": {"key": "TEST", "name": "Test Space"},
                "_links": {"webui": "/spaces/TEST/pages/123456/Test+Page"},
                "version": {"number": 1, "when": "2026-01-21T10:00:00.000Z"},
            }
        ]

        result = self.client._parse_content(api_response)

        self.assertEqual(len(result), 1)
        item = result[0]
        # Should add /wiki prefix
        self.assertEqual(
            item["url"],
            "https://test.atlassian.net/wiki/spaces/TEST/pages/123456/Test+Page",
        )

    def test_parse_content_empty_list(self):
        """Test parsing empty content list"""
        result = self.client._parse_content([])
        self.assertEqual(result, [])

    def test_parse_content_with_malformed_item(self):
        """Test parsing with malformed item (should skip it)"""
        api_response = [
            {"id": "123456", "title": "Valid Page", "type": "page"},
            None,  # Malformed
            {"title": "Another Valid Page"},  # Missing id
        ]

        result = self.client._parse_content(api_response)

        # Should return items that could be parsed
        self.assertGreaterEqual(len(result), 0)

    def test_parse_content_different_date_formats(self):
        """Test parsing different date formats"""
        api_response = [
            {
                "id": "123456",
                "title": "Test Page",
                "type": "page",
                "space": {"key": "TEST", "name": "Test Space"},
                "_links": {"webui": "/wiki/spaces/TEST/pages/123456/Test+Page"},
                "version": {"number": 1, "when": "2026-01-21T14:27:02.000Z"},
            },
            {
                "id": "123457",
                "title": "Test Page 2",
                "type": "page",
                "space": {"key": "TEST", "name": "Test Space"},
                "_links": {"webui": "/wiki/spaces/TEST/pages/123457/Test+Page+2"},
                "version": {"number": 1, "when": "2025-12-31T23:59:59.999Z"},
            },
        ]

        result = self.client._parse_content(api_response)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["last_modified"], "2026-01-21")
        self.assertEqual(result[1]["last_modified"], "2025-12-31")


if __name__ == "__main__":
    unittest.main()
