# Claude Code Issue Triage — Project Context

## What we're building
A parser and analysis toolkit that pulls open issues from the 
anthropics/claude-code GitHub repo, categorizes them, and 
synthesizes themes for product team triage.

This is a take-home assignment for the Product Operations Manager, 
Public Sector role at Anthropic.

## The objective (from the brief)
Synthesize user feedback at scale, identify actionable themes, and 
design systems that connect users to product teams — core to the 
"Inputs to Product Teams" pillar of Product Operations.

## Deliverables
1. Categorized issue tracker (spreadsheet) — 100+ issues tagged 
   with category, priority, summary
2. Themes synthesis memo (1-2 pages) — top 5-7 themes with counts
3. Prioritization framework + top 10 issues to address first
4. User communication strategy with 2-3 sample messages
5. Internal validation plan (who to pressure-test with)
6. Evergreen program proposal (how this becomes ongoing)

Final format: single PDF or Google Drive folder.

## Hard constraints
- READ-ONLY: Never comment on, modify, label, or interact with 
  actual GitHub issues. All work is local.
- Time-box: This is a 2-3 hour exercise. Optimize for thoughtful 
  work on a subset over comprehensive but shallow coverage.
- Use the gh CLI for GitHub API calls when possible (already 
  authenticated).

## Repo conventions
- /src — reusable parser code as importable Python modules (.py)
- /notebooks — Jupyter notebooks for exploration and analysis (.ipynb)
- /data — raw and processed issue data (gitignored)
- /deliverables — final memos, spreadsheet, comms drafts (markdown, PDF, xlsx)
- /docs — assignment brief, notes, references

## Working preferences
- Show your thinking. Frameworks and rationale matter as much 
  as outputs.
- Prefer Python for data work, markdown for written deliverables.
- When proposing categorizations or frameworks, suggest 2-3 
  options with tradeoffs rather than picking unilaterally.
- Ask before running anything that writes outside this repo.
- When working in notebooks, keep cells small and narrate decisions 
  in markdown cells. Clear outputs before committing.
- Move any function used more than once from a notebook into /src 
  as an importable module.

## What "good" looks like
- A categorization schema that's defined and consistent
- Theme counts backed by the data, not vibes
- Prioritization rationale a PM could defend in a meeting
- Comms drafts that sound like a human, not a status bot
- An evergreen program that's lightweight enough to actually run