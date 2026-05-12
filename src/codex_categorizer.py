"""
Issue categorization and priority scoring for openai/codex GitHub issues.

Mirrors the interface of categorizer.py but adapts to the openai/codex label
taxonomy and the slightly different field shape returned by `gh issue list`
(comments is a list, reactionGroups is a list of dicts, author replaces user).
"""

from typing import Any

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

AREA_MAP = {
    "app":           "Desktop App",
    "app-server":    "App Server",
    "CLI":           "Core / CLI",
    "TUI":           "TUI / Interface",
    "browser":       "Browser / Web",
    "codex-web":     "Browser / Web",
    "extension":     "IDE Extension",
    "mcp":           "MCP",
    "mcp-server":    "MCP",
    "tool-calls":    "Tools",
    "sandbox":       "Sandbox",
    "auth":          "Auth / Permissions",
    "session":       "Session / Context",
    "context":       "Session / Context",
    "memory":        "Session / Context",
    "skills":        "Skills",
    "hooks":         "Hooks",
    "subagent":      "Agents",
    "agent":         "Agents",
    "automations":   "Automations",
    "connectivity":  "Connectivity / Networking",
    "rate-limits":   "Connectivity / Networking",
    "performance":   "Performance",
    "config":        "Config",
    "custom-model":  "Custom Models",
    "model-behavior":"Model / AI Behavior",
    "safety-check":  "Model / AI Behavior",
    "computer-use":  "Computer Use",
    "remote":        "Remote Execution",
    "exec":          "Remote Execution",
    "plan":          "Planning",
    "pets":          "Persistence / Pets",
    "imagen":        "Image Generation",
    "code-review":   "Code Review",
    "enterprise":    "Enterprise",
    "azure":         "Enterprise",
    "sdk":           "SDK",
    "documentation": "Docs",
    "windows-os":    "Windows",
    "macOS":         "macOS",
    "iOS":           "iOS",
}

_PRIORITY_LABEL = {"P0": "High", "P1": "High", "P2": "Medium", "P3": "Low"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label_names(issue: dict) -> list[str]:
    return [l["name"] for l in issue.get("labels", [])]


def _comment_count(issue: dict) -> int:
    c = issue.get("comments", [])
    return len(c) if isinstance(c, list) else int(c)


def _reaction_total(issue: dict) -> int:
    return sum(
        rg.get("users", {}).get("totalCount", 0)
        for rg in issue.get("reactionGroups", [])
    )


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------

def assign_area(issue: dict) -> str:
    for label in _label_names(issue):
        if label in AREA_MAP:
            return AREA_MAP[label]
    title = issue.get("title", "").lower()
    if any(w in title for w in ("install", "setup", "start")):
        return "Installation / Setup"
    if any(w in title for w in ("cost", "token", "billing", "credit")):
        return "Cost / Token Usage"
    if any(w in title for w in ("mcp",)):
        return "MCP"
    if any(w in title for w in ("model", "hallucin", "gpt", "openai")):
        return "Model / AI Behavior"
    if any(w in title for w in ("auth", "login", "api key", "oauth")):
        return "Auth / Permissions"
    return "Other"


def assign_priority(issue: dict) -> str:
    """
    P0 — safety-check label
    P1 — regression or high-engagement bug (10+ reactions + comments)
    P2 — moderate-engagement bug (5+) or high-engagement enhancement
    P3 — everything else
    """
    labels = set(_label_names(issue))
    engagement = _reaction_total(issue) + _comment_count(issue)

    if "safety-check" in labels:
        return "P0"
    if "regression" in labels:
        return "P1"
    if "bug" in labels:
        if engagement >= 10:
            return "P1"
        if engagement >= 5:
            return "P2"
        return "P3"
    if "enhancement" in labels:
        if engagement >= 10:
            return "P2"
        return "P3"
    return "P3"


def brief_summary(issue: dict, max_chars: int = 160) -> str:
    body = (issue.get("body") or "").strip()
    if not body:
        return ""
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("#", ">", "-", "*", "|", "!", "[")):
            continue
        if line.endswith(":") and len(line) < 60:
            continue
        sentence_end = min(
            (line.find(c) for c in ".!?" if line.find(c) != -1),
            default=-1,
        )
        if 0 < sentence_end < max_chars:
            return line[:sentence_end + 1]
        return line[:max_chars] + ("…" if len(line) > max_chars else "")
    return body[:max_chars] + ("…" if len(body) > max_chars else "")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def triage_row(issue: dict) -> dict[str, Any]:
    """Return a triage-tracker row matching the schema of triage_row() in categorizer.py."""
    labels = _label_names(issue)
    label_set = set(labels)
    area = assign_area(issue)
    p_code = assign_priority(issue)

    type_labels = [l for l in labels if l in ("bug", "enhancement", "regression")]
    category = " · ".join(dict.fromkeys([area] + type_labels))

    title = issue.get("title", "").strip()
    title = title[:100] + ("…" if len(title) > 100 else "")

    return {
        "Issue #":          issue["number"],
        "Title":            title,
        "Category/Tag(s)":  category,
        "Priority":         _PRIORITY_LABEL[p_code],
        "Bug":              "Yes" if "bug" in label_set else "No",
        "Enhancement":      "Yes" if "enhancement" in label_set else "No",
        "Regression":       "Yes" if "regression" in label_set else "No",
        "Question":         "Yes" if "question" in label_set else "No",
        "Brief Summary":    brief_summary(issue),
    }
