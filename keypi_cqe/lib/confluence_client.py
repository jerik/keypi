"""
Confluence Cloud REST API v1 Client
Handles authentication and CQL queries
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from base64 import b64encode


class ConfluenceClient:
    """Wrapper for Confluence Cloud REST API v1"""

    def __init__(self, confluence_url, email, api_token):
        """
        Initialize Confluence client with authentication credentials

        Args:
            confluence_url: Base URL of Confluence Cloud instance (e.g., https://your-domain.atlassian.net)
            email: Atlassian account email
            api_token: Atlassian API token
        """
        self.confluence_url = confluence_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.timeout = 10  # seconds

    def _get_auth_header(self):
        """Generate Basic Auth header for Atlassian API"""
        credentials = f"{self.email}:{self.api_token}"
        encoded = b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def search_content(self, cql_query, max_results=50):
        """
        Search Confluence content using CQL

        Args:
            cql_query: CQL query string
            max_results: Maximum number of results to return (default: 50)

        Returns:
            List of content items with parsed fields, or None on error

        Raises:
            ConfluenceAuthError: Authentication failed (401/403)
            ConfluenceAPIError: API error occurred
            ConfluenceNetworkError: Network/connection error
        """
        # Construct API endpoint
        endpoint = f"{self.confluence_url}/wiki/rest/api/content/search"

        # Build query parameters
        # expand: Get full space and version details
        params = {
            "cql": cql_query,
            "limit": max_results,
            "start": 0,
            "expand": "space,version",
        }

        url = f"{endpoint}?{urllib.parse.urlencode(params)}"

        # Create request with authentication
        request = urllib.request.Request(url)
        request.add_header("Authorization", self._get_auth_header())
        request.add_header("Accept", "application/json")
        request.add_header("Content-Type", "application/json")

        try:
            # Execute request
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())

            results = data.get("results", [])

            # Log first raw result for debugging (sample only)
            if results and len(results) > 0:
                sample = results[0]
                print(
                    f"[CQE-DEBUG] Raw API sample: id={sample.get('id')}, "
                    f"space={sample.get('space', {})}, "
                    f"version={sample.get('version', {})}"
                )

            # Parse and return content items
            return self._parse_content(results)

        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise ConfluenceAuthError(
                    f"Authentication failed: {e.code} {e.reason}. "
                    "Please check your API token and email in the configuration."
                )
            elif e.code == 429:
                raise ConfluenceAPIError(
                    "Rate limit exceeded. Please wait before making more requests."
                )
            elif e.code == 400:
                raise ConfluenceAPIError(
                    f"Invalid CQL query: {e.reason}. Please check your query syntax."
                )
            else:
                raise ConfluenceAPIError(f"Confluence API error: {e.code} {e.reason}")

        except urllib.error.URLError as e:
            raise ConfluenceNetworkError(
                f"Network error: {e.reason}. Please check your internet connection."
            )

        except Exception as e:
            raise ConfluenceAPIError(f"Unexpected error: {str(e)}")

    def _parse_content(self, content_items):
        """
        Parse Confluence content from API response

        Args:
            content_items: Raw content list from API response

        Returns:
            List of parsed content dictionaries
        """
        parsed_content = []

        for item in content_items:
            try:
                # Extract basic fields
                content_id = item.get("id", "")
                title = item.get("title", "Untitled")
                content_type = item.get("type", "unknown")

                # Extract space information
                space = item.get("space", {})
                space_key = space.get("key", "")
                space_name = space.get("name", "Unknown Space")

                # Extract web URL from _links
                links = item.get("_links", {})
                webui = links.get("webui", "")

                # Construct full URL with /wiki prefix
                if webui:
                    # Ensure the webui path has /wiki prefix
                    wiki_path = webui if webui.startswith("/wiki") else f"/wiki{webui}"
                    full_url = f"{self.confluence_url}{wiki_path}"
                else:
                    full_url = ""

                # Extract version info
                version = item.get("version", {})
                version_number = version.get("number", 0)
                last_modified = version.get("when", "")

                # Format lastModified as ISO date (YYYY-MM-DD)
                last_modified_date = ""
                if last_modified:
                    # Expected format: 2026-01-21T14:27:02.000Z
                    # Extract just the date part
                    last_modified_date = last_modified.split("T")[0]

                parsed_item = {
                    "id": content_id,
                    "title": title,
                    "type": content_type,
                    "space_key": space_key,
                    "space_name": space_name,
                    "version": version_number,
                    "last_modified": last_modified_date,
                    "url": full_url,
                    "webui": webui,
                }

                parsed_content.append(parsed_item)

            except Exception:
                # Skip items that fail to parse
                continue

        return parsed_content


# Custom exceptions
class ConfluenceAuthError(Exception):
    """Raised when authentication fails"""

    pass


class ConfluenceAPIError(Exception):
    """Raised when API returns an error"""

    pass


class ConfluenceNetworkError(Exception):
    """Raised when network error occurs"""

    pass
