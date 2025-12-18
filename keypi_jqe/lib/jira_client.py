"""
Jira Cloud REST API v3 Client
Handles authentication and JQL queries
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from base64 import b64encode


class JiraClient:
    """Wrapper for Jira Cloud REST API v3"""

    def __init__(self, jira_url, email, api_token):
        """
        Initialize Jira client with authentication credentials

        Args:
            jira_url: Base URL of Jira Cloud instance (e.g., https://your-domain.atlassian.net)
            email: Atlassian account email
            api_token: Atlassian API token
        """
        self.jira_url = jira_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.timeout = 10  # seconds

    def _get_auth_header(self):
        """Generate Basic Auth header for Atlassian API"""
        credentials = f"{self.email}:{self.api_token}"
        encoded = b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def search_issues(self, jql_query, max_results=50):
        """
        Search Jira issues using JQL

        Args:
            jql_query: JQL query string
            max_results: Maximum number of results to return (default: 50)

        Returns:
            List of issues with parsed fields, or None on error

        Raises:
            JiraAuthError: Authentication failed (401/403)
            JiraAPIError: API error occurred
            JiraNetworkError: Network/connection error
        """
        # Construct API endpoint
        endpoint = f"{self.jira_url}/rest/api/3/search/jql"

        # Define fields to retrieve
        fields = [
            "summary",
            "status",
            "priority",
            "creator",
            "assignee",
            "created"
        ]

        # Build query parameters
        params = {
            "jql": jql_query,
            "maxResults": max_results,
            "fields": ",".join(fields)
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

            # Parse and return issues
            return self._parse_issues(data.get("issues", []))

        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise JiraAuthError(
                    f"Authentication failed: {e.code} {e.reason}. "
                    "Please check your API token and email in the configuration."
                )
            elif e.code == 429:
                raise JiraAPIError(
                    "Rate limit exceeded. Please wait before making more requests."
                )
            elif e.code == 400:
                raise JiraAPIError(
                    f"Invalid JQL query: {e.reason}. Please check your query syntax."
                )
            else:
                raise JiraAPIError(
                    f"Jira API error: {e.code} {e.reason}"
                )

        except urllib.error.URLError as e:
            raise JiraNetworkError(
                f"Network error: {e.reason}. Please check your internet connection."
            )

        except Exception as e:
            raise JiraAPIError(f"Unexpected error: {str(e)}")

    def _parse_issues(self, issues):
        """
        Parse Jira issues from API response

        Args:
            issues: Raw issues list from API response

        Returns:
            List of parsed issue dictionaries
        """
        parsed_issues = []

        for issue in issues:
            try:
                fields = issue.get("fields", {})

                # Extract status
                status = fields.get("status", {})
                status_name = status.get("name", "Unknown")

                # Extract priority
                priority = fields.get("priority", {})
                priority_name = priority.get("name", "None")

                # Extract creator
                creator = fields.get("creator", {})
                creator_name = creator.get("displayName", "Unknown")

                # Extract assignee
                assignee = fields.get("assignee")
                assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"

                parsed_issue = {
                    "key": issue.get("key", ""),
                    "summary": fields.get("summary", "No summary"),
                    "status": status_name,
                    "priority": priority_name,
                    "creator": creator_name,
                    "assignee": assignee_name,
                    "created": fields.get("created", ""),
                    "url": f"{self.jira_url}/browse/{issue.get('key', '')}"
                }

                parsed_issues.append(parsed_issue)

            except Exception:
                # Skip issues that fail to parse
                continue

        return parsed_issues


# Custom exceptions
class JiraAuthError(Exception):
    """Raised when authentication fails"""
    pass


class JiraAPIError(Exception):
    """Raised when API returns an error"""
    pass


class JiraNetworkError(Exception):
    """Raised when network error occurs"""
    pass
