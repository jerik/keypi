"""
Jira Cloud REST API v3 Client - User Search
Handles authentication and user search queries
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from base64 import b64encode


class UserClient:
    """Wrapper for Jira Cloud User Search API"""

    def __init__(self, jira_url, email, api_token):
        """
        Initialize User client with authentication credentials

        Args:
            jira_url: Base URL of Jira Cloud instance (e.g., https://your-domain.atlassian.net)
            email: Atlassian account email
            api_token: Atlassian API token
        """
        self.jira_url = jira_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.timeout = 10  # seconds

    def _get_auth_header(self):
        """Generate Basic Auth header for Atlassian API"""
        credentials = f"{self.email}:{self.api_token}"
        encoded = b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def search_users(self, query, max_results=50, save_raw_response_path=None):
        """
        Search Jira users by query string

        Args:
            query: Search string (name, email, etc.)
            max_results: Maximum number of results to return (default: 50)
            save_raw_response_path: Optional path to save raw JSON response for debugging

        Returns:
            List of users with parsed fields

        Raises:
            UserAuthError: Authentication failed (401/403)
            UserAPIError: API error occurred
            UserNetworkError: Network/connection error
        """
        # Construct API endpoint: /rest/api/3/user/search
        endpoint = f"{self.jira_url}/rest/api/3/user/search"

        # Build query parameters
        params = {
            "query": query,
            "maxResults": max_results,
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
                raw_data = response.read().decode()
                data = json.loads(raw_data)

            # Save raw response for debugging if path provided
            if save_raw_response_path:
                with open(save_raw_response_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            # Parse and return users
            return self._parse_users(data)

        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise UserAuthError(
                    f"Authentication failed: {e.code} {e.reason}. "
                    "Please check your API token and email in the configuration."
                )
            elif e.code == 429:
                raise UserAPIError(
                    "Rate limit exceeded. Please wait before making more requests."
                )
            elif e.code == 400:
                raise UserAPIError(
                    f"Invalid query: {e.reason}. Please check your search term."
                )
            else:
                raise UserAPIError(f"Jira API error: {e.code} {e.reason}")

        except urllib.error.URLError as e:
            raise UserNetworkError(
                f"Network error: {e.reason}. Please check your internet connection."
            )

        except Exception as e:
            raise UserAPIError(f"Unexpected error: {str(e)}")

    def _parse_users(self, users):
        """
        Parse Jira users from API response

        Args:
            users: Raw users list from API response (array of user objects)

        Returns:
            List of parsed user dictionaries
        """
        parsed_users = []

        for user in users:
            try:
                # Extract fields - emailAddress might be None due to privacy settings
                account_id = user.get("accountId", "")
                display_name = user.get("displayName", "Unknown")
                email_address = user.get("emailAddress")  # May be None!
                active = user.get("active", False)
                account_type = user.get("accountType", "atlassian")

                # Build profile URL
                profile_url = f"{self.jira_url}/jira/people/{account_id}"

                parsed_user = {
                    "account_id": account_id,
                    "display_name": display_name,
                    "email": email_address,  # None if not available
                    "active": active,
                    "account_type": account_type,
                    "profile_url": profile_url,
                }

                parsed_users.append(parsed_user)

            except Exception:
                # Skip users that fail to parse
                continue

        return parsed_users


# Custom exceptions
class UserAuthError(Exception):
    """Raised when authentication fails"""

    pass


class UserAPIError(Exception):
    """Raised when API returns an error"""

    pass


class UserNetworkError(Exception):
    """Raised when network error occurs"""

    pass
