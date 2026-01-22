"""
Unit tests for URL transformations (edit mode, etc.)
"""

import unittest
import re


class TestURLTransformations(unittest.TestCase):
    """Test URL transformation functions"""

    def _generate_edit_url(self, page_url, page_id):
        """
        Generate edit URL from view URL
        (Copy of the implementation from __init__.py for testing)

        Normal URL: <confluence-url>/wiki/spaces/FOO/pages/687210497/foobar-seite
        Edit URL: <confluence-url>/wiki/spaces/FOO/pages/edit-v2/687210497

        Args:
            page_url: Normal page URL
            page_id: Page ID

        Returns:
            Edit mode URL
        """
        # Extract base URL and space key from page URL
        # Pattern: <base>/wiki/spaces/<SPACE>/pages/<ID>/...
        match = re.match(r"(.*?/wiki/spaces/[^/]+)/pages/\d+", page_url)
        if match:
            base_path = match.group(1)
            edit_url = f"{base_path}/pages/edit-v2/{page_id}"
            return edit_url
        else:
            # Fallback: use page_url as-is
            return page_url

    def test_generate_edit_url_standard(self):
        """Test edit URL generation for standard page URL"""
        page_url = (
            "https://test.atlassian.net/wiki/spaces/FOO/pages/687210497/foobar-seite"
        )
        page_id = "687210497"

        result = self._generate_edit_url(page_url, page_id)

        expected = "https://test.atlassian.net/wiki/spaces/FOO/pages/edit-v2/687210497"
        self.assertEqual(result, expected)

    def test_generate_edit_url_with_plus_signs(self):
        """Test edit URL generation with + signs in title"""
        page_url = (
            "https://test.atlassian.net/wiki/spaces/DEV/pages/123456/My+Test+Page"
        )
        page_id = "123456"

        result = self._generate_edit_url(page_url, page_id)

        expected = "https://test.atlassian.net/wiki/spaces/DEV/pages/edit-v2/123456"
        self.assertEqual(result, expected)

    def test_generate_edit_url_with_encoded_characters(self):
        """Test edit URL generation with URL-encoded characters"""
        page_url = "https://test.atlassian.net/wiki/spaces/DOCS/pages/999888/Test%20Page%20%28v2%29"
        page_id = "999888"

        result = self._generate_edit_url(page_url, page_id)

        expected = "https://test.atlassian.net/wiki/spaces/DOCS/pages/edit-v2/999888"
        self.assertEqual(result, expected)

    def test_generate_edit_url_short_space_name(self):
        """Test edit URL generation with single-letter space key"""
        page_url = "https://test.atlassian.net/wiki/spaces/X/pages/111/test"
        page_id = "111"

        result = self._generate_edit_url(page_url, page_id)

        expected = "https://test.atlassian.net/wiki/spaces/X/pages/edit-v2/111"
        self.assertEqual(result, expected)

    def test_generate_edit_url_different_page_id(self):
        """Test edit URL generation where URL ID and page_id differ (should use page_id)"""
        page_url = "https://test.atlassian.net/wiki/spaces/FOO/pages/111111/test"
        page_id = "222222"  # Different from URL

        result = self._generate_edit_url(page_url, page_id)

        # Should use the provided page_id, not the one from URL
        expected = "https://test.atlassian.net/wiki/spaces/FOO/pages/edit-v2/222222"
        self.assertEqual(result, expected)

    def test_generate_edit_url_malformed_url(self):
        """Test edit URL generation with malformed URL (fallback)"""
        page_url = "https://test.atlassian.net/invalid/format"
        page_id = "123456"

        result = self._generate_edit_url(page_url, page_id)

        # Should return original URL as fallback
        self.assertEqual(result, page_url)

    def test_generate_edit_url_without_trailing_path(self):
        """Test edit URL generation without page title in path"""
        page_url = "https://test.atlassian.net/wiki/spaces/FOO/pages/123456"
        page_id = "123456"

        result = self._generate_edit_url(page_url, page_id)

        expected = "https://test.atlassian.net/wiki/spaces/FOO/pages/edit-v2/123456"
        self.assertEqual(result, expected)

    def test_generate_edit_url_long_space_key(self):
        """Test edit URL generation with long space key"""
        page_url = "https://test.atlassian.net/wiki/spaces/VERY_LONG_SPACE_KEY_123/pages/999/test"
        page_id = "999"

        result = self._generate_edit_url(page_url, page_id)

        expected = "https://test.atlassian.net/wiki/spaces/VERY_LONG_SPACE_KEY_123/pages/edit-v2/999"
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
