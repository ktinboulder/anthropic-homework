"""
Issue categorization and priority scoring for anthropics/claude-code GitHub issues.
"""

import re
from typing import Any

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

AREA_MAP = {
    "area:tui": "TUI / Interface",
    "area:core": "Core / CLI",
    "area:cli": "Core / CLI",
    "area:bash": "Core / CLI",
    "area:model": "Model / AI Behavior",
    "area:model-behavior": "Model / AI Behavior",
    "area:cost": "Cost / Token Usage",
    "area:mcp": "MCP",
    "area:auth": "Auth / Permissions",
    "area:permissions": "Auth / Permissions",
    "area:agents": "Agents",
    "area:ide": "IDE Integration",
    "area:vscode": "IDE Integration",
    "area:desktop": "Desktop App",
    "area:installation": "Installation / Setup",
    "area:tools": "Tools",
    "area:cowork": "Cowork",
    "area:skills": "Skills",
    "area:hooks": "Hooks",
    "area:plugins": "Plugins",
    "area:sandbox": "Sandbox",
    "area:security": "Security",
    "area:api": "API",
    "area:networking": "Networking",
    "area:ui": "TUI / Interface",
    "area:chrome": "Chrome / Browser",
    "area:browser-extension": "Chrome / Browser",
    "area:integrations": "Integrations",
    "area:docs": "Docs",
    "area:packaging": "Installation / Setup",
    "memory": "Memory / Context",
}

PLATFORM_MAP = {
    "platform:macos": "macOS",
    "platform:windows": "Windows",
    "platform:linux": "Linux",
    "platform:vscode": "VS Code",
    "platform:intellij": "IntelliJ",
    "platform:wsl": "WSL",
    "platform:web": "Web",
}

TYPE_MAP = {
    "bug": "Bug",
    "regression": "Regression",
    "enhancement": "Enhancement",
    "duplicate": "Duplicate",
    "invalid": "Invalid",
    "external": "External",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label_names(issue: dict) -> list[str]:
    return [l["name"] for l in issue.get("labels", [])]


def _reaction_total(issue: dict) -> int:
    r = issue.get("reactions", {})
    if not r:
        return 0
    return sum(v for k, v in r.items() if k not in ("url", "total_count") and isinstance(v, int))


def _has_label(issue: dict, *labels: str) -> bool:
    names = set(_label_names(issue))
    return any(l in names for l in labels)


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------

def assign_type(issue: dict) -> str:
    labels = _label_names(issue)
    for label in ("regression", "bug", "enhancement", "duplicate", "invalid", "external"):
        if label in labels:
            return TYPE_MAP[label]
    return "Other"


def assign_area(issue: dict) -> str:
    labels = _label_names(issue)
    for label in labels:
        if label in AREA_MAP:
            return AREA_MAP[label]
    # Fallback: infer from title keywords
    title = issue.get("title", "").lower()
    if any(w in title for w in ("install", "setup", "start")):
        return "Installation / Setup"
    if any(w in title for w in ("cost", "token", "billing")):
        return "Cost / Token Usage"
    if any(w in title for w in ("mcp", "server")):
        return "MCP"
    if any(w in title for w in ("model", "claude", "hallucin")):
        return "Model / AI Behavior"
    if any(w in title for w in ("auth", "login", "api key")):
        return "Auth / Permissions"
    if any(w in title for w in ("permission", "allow", "deny")):
        return "Auth / Permissions"
    if any(w in title for w in ("memory", "context")):
        return "Memory / Context"
    return "Other"


def assign_platform(issue: dict) -> str:
    labels = _label_names(issue)
    platforms = [PLATFORM_MAP[l] for l in labels if l in PLATFORM_MAP]
    return ", ".join(platforms) if platforms else "Cross-platform"


def assign_priority(issue: dict) -> str:
    """
    P0 — data loss or security
    P1 — regression or blocker signal (high reactions + has-repro)
    P2 — bug with repro or high engagement enhancement
    P3 — everything else
    """
    labels = set(_label_names(issue))
    reactions = _reaction_total(issue)
    comments = issue.get("comments", 0)
    engagement = reactions + comments

    if "data-loss" in labels or "area:security" in labels:
        return "P0"

    if "regression" in labels:
        return "P1"

    if "bug" in labels:
        if "has repro" in labels and engagement >= 5:
            return "P1"
        if "has repro" in labels or engagement >= 10:
            return "P2"
        return "P3"

    if "enhancement" in labels:
        if engagement >= 15:
            return "P2"
        return "P3"

    return "P3"


_PRIORITY_LABEL = {"P0": "High", "P1": "High", "P2": "Medium", "P3": "Low"}


def summarize_title(issue: dict) -> str:
    """Trim long titles to 100 chars."""
    title = issue.get("title", "").strip()
    return title[:100] + ("…" if len(title) > 100 else "")


def brief_summary(issue: dict, max_chars: int = 160) -> str:
    """Extract a short human-readable summary from the issue body.

    Skips template headers (lines ending with ':' or starting with '#'/'>'),
    then returns the first substantive sentence or fragment up to max_chars.
    """
    body = (issue.get("body") or "").strip()
    if not body:
        return ""

    for line in body.splitlines():
        line = line.strip()
        # Skip blank lines, markdown headers, blockquotes, and template labels
        if not line:
            continue
        if line.startswith(("#", ">", "-", "*", "|", "!")):
            continue
        if line.endswith(":") and len(line) < 60:
            continue
        # Found a substantive line — truncate at sentence boundary if possible
        sentence_end = min(
            (line.find(c) for c in ".!?" if line.find(c) != -1),
            default=-1,
        )
        if 0 < sentence_end < max_chars:
            return line[: sentence_end + 1]
        return line[:max_chars] + ("…" if len(line) > max_chars else "")

    return body[:max_chars] + ("…" if len(body) > max_chars else "")


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def categorize(issue: dict) -> dict[str, Any]:
    labels = _label_names(issue)
    return {
        "number": issue["number"],
        "title": summarize_title(issue),
        "url": issue.get("html_url", ""),
        "type": assign_type(issue),
        "area": assign_area(issue),
        "platform": assign_platform(issue),
        "priority": assign_priority(issue),
        "labels": ", ".join(labels),
        "comments": issue.get("comments", 0),
        "reactions": _reaction_total(issue),
        "has_repro": "has repro" in labels,
        "created_at": issue.get("created_at", "")[:10],
        "updated_at": issue.get("updated_at", "")[:10],
        "author": (issue.get("user") or {}).get("login", ""),
    }


def triage_row(issue: dict) -> dict[str, Any]:
    """Return a triage-focused row for the simplified issue tracker spreadsheet.

    Columns: Issue #, Title, Category/Tag(s), Priority (High/Medium/Low),
             Brief Summary.
    """
    labels = _label_names(issue)
    p_code = assign_priority(issue)
    area = assign_area(issue)
    issue_type = assign_type(issue)

    # Category/Tag(s): combine area + type, plus any area: labels for detail
    area_labels = [l for l in labels if l.startswith("area:")]
    category_parts = [area, issue_type]
    if area_labels:
        category_parts.append(", ".join(area_labels))
    category = " · ".join(dict.fromkeys(category_parts))  # dedupe, preserve order

    return {
        "Issue #": issue["number"],
        "Title": summarize_title(issue),
        "Category/Tag(s)": category,
        "Priority": _PRIORITY_LABEL[p_code],
        "Brief Summary": brief_summary(issue),
    }
