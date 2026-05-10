"""
Rank issue reporters by a composite GitHub profile score.

Score components:
  - followers:  log(followers + 1) * 10   — community standing, log-scaled
  - repos:      min(repos, 100) * 0.2     — contribution breadth, capped
  - tenure:     min(years, 10) * 1.5      — account age proxy, capped at 10y
  - issues:     count * 2                 — volume of engagement with this product

Note: GitHub achievement badges are not exposed via the REST or GraphQL API
and are therefore excluded from this score.
"""

import json
import math
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def count_reporters(issues: list[dict]) -> Counter:
    """Return a Counter of {login: issue_count} from a list of issue dicts."""
    counts: Counter = Counter()
    for issue in issues:
        user = issue.get("user") or {}
        login = user.get("login")
        if login:
            counts[login] += 1
    return counts


def fetch_user_profile(login: str, delay: float = 0.3) -> Optional[dict]:
    """Fetch a GitHub user profile via the gh CLI. Returns None on failure."""
    result = subprocess.run(
        [
            "gh", "api", f"users/{login}",
            "--jq",
            "{login:.login,name:.name,followers:.followers,"
            "public_repos:.public_repos,public_gists:.public_gists,"
            "created_at:.created_at}",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    time.sleep(delay)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def compute_score(profile: dict, issue_count: int) -> dict:
    """Compute composite ranking score for one reporter."""
    now = datetime.now(timezone.utc)
    followers = profile.get("followers") or 0
    repos = profile.get("public_repos") or 0
    created_at = profile.get("created_at", "")
    tenure_years = 0.0
    if created_at:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        tenure_years = (now - created).days / 365.25

    follower_score = math.log1p(followers) * 10
    repo_score = min(repos, 100) * 0.2
    tenure_score = min(tenure_years, 10) * 1.5
    issue_score = issue_count * 2
    total = follower_score + repo_score + tenure_score + issue_score

    return {
        "login": profile["login"],
        "name": profile.get("name") or "",
        "followers": followers,
        "public_repos": repos,
        "tenure_years": round(tenure_years, 1),
        "issues_reported": issue_count,
        "follower_score": round(follower_score, 1),
        "repo_score": round(repo_score, 1),
        "tenure_score": round(tenure_score, 1),
        "issue_score": issue_score,
        "total_score": round(total, 1),
    }


def rank_reporters(
    issues: list[dict],
    top_n: int = 10,
    candidate_pool: int = 30,
    fetch_delay: float = 0.3,
) -> list[dict]:
    """Return the top N reporters ranked by composite score.

    Args:
        issues:         Raw issue dicts (must contain a 'user' key).
        top_n:          Number of results to return.
        candidate_pool: How many top-by-volume reporters to fetch profiles for.
        fetch_delay:    Seconds between gh API calls to avoid rate limiting.

    Returns:
        List of score dicts, sorted descending by total_score.
    """
    counts = count_reporters(issues)
    candidates = [login for login, _ in counts.most_common(candidate_pool)]

    scored = []
    for login in candidates:
        profile = fetch_user_profile(login, delay=fetch_delay)
        if profile:
            scored.append(compute_score(profile, counts[login]))

    return sorted(scored, key=lambda x: x["total_score"], reverse=True)[:top_n]


def format_markdown_table(ranked: list[dict]) -> str:
    """Render ranked reporters as a markdown table."""
    lines = [
        "| Rank | Login | Name | Followers | Repos | Tenure | Issues | Score |",
        "|------|-------|------|----------:|------:|-------:|-------:|------:|",
    ]
    for i, r in enumerate(ranked, 1):
        link = f"[{r['login']}](https://github.com/{r['login']})"
        lines.append(
            f"| {i} | {link} | {r['name']} | {r['followers']} "
            f"| {r['public_repos']} | {r['tenure_years']}y "
            f"| {r['issues_reported']} | **{r['total_score']}** |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rank Claude Code issue reporters.")
    parser.add_argument("issues_json", help="Path to raw issues JSON file")
    parser.add_argument("--top", type=int, default=10, help="Number of results")
    parser.add_argument("--pool", type=int, default=30, help="Candidate pool size")
    args = parser.parse_args()

    issues = json.loads(Path(args.issues_json).read_text())
    ranked = rank_reporters(issues, top_n=args.top, candidate_pool=args.pool)

    print(format_markdown_table(ranked))
    print(f"\nFull data written to stdout. Use --top and --pool to adjust.")
