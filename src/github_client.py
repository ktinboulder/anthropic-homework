"""
GitHub REST API client for fetching issues from a public repo.

Uses GITHUB_TOKEN from the environment for authentication.
"""

import os
import requests
from typing import Optional


_BASE = "https://api.github.com"


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN is not set")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def fetch_issues(
    repo: str,
    state: str = "open",
    limit: int = 30,
    fields: Optional[list[str]] = None,
) -> list[dict]:
    """Fetch issues from a GitHub repo via the REST API.

    Args:
        repo:   Owner/repo string, e.g. "anthropics/claude-code".
        state:  "open", "closed", or "all".
        limit:  Max issues to return. Paginates automatically (100 per page).
        fields: Optional list of top-level field names to keep. Returns all
                fields when None.

    Returns:
        List of issue dicts. Pull requests are excluded.
    """
    url = f"{_BASE}/repos/{repo}/issues"
    headers = _headers()
    issues: list[dict] = []
    page = 1

    while len(issues) < limit:
        params = {"state": state, "per_page": 100, "page": page}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        issues.extend(i for i in batch if "pull_request" not in i)
        page += 1

    issues = issues[:limit]

    if fields:
        issues = [{k: v for k, v in i.items() if k in fields} for i in issues]

    return issues
