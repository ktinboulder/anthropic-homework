# How this analysis gets made

> A working note on the Claude-in-the-loop workflow behind the weekly Claude Code issue analysis. Less a process doc, more a tour of the stack — what's automated, what's human, and what gets faster as we run it more.

---

## The thesis

At 1,000 issues per cut, the work splits cleanly into two layers: **mechanical** (pulling, classifying, clustering, drafting) and **judgmental** (severity calls on edge cases, framing, recommended actions, customer-specific signal). Claude does the mechanical layer end-to-end. I do the judgmental layer on top of its output.

End-to-end run time: **~2 hours of human time per week**, most of it judgment.

---

## The stack

| Tool | Role | What it does |
|---|---|---|
| **Claude Code + Jupyter** | Data pipeline | Pulls issues from the GitHub API, enriches with priority / area / regression flags, exports `triage_tracker.xlsx` |
| **Claude Chat (project)** | Synthesis layer | Theme clustering, draft memo synthesis, comparison against prior weeks. Long-running project context — every prior week's analysis is in scope. |
| **Console prompt generator** | Prompt scaffolding | First-pass prompts for new artifact types (comms templates, prioritization frameworks). I refine; Claude Chat executes. |
| **Claude Chat (critic mode)** | Self-grading | I prompt Claude to grade my draft as the recipient (audience profile loaded). Catches tone misses, AI-generated feel, missing context. |
| **Manual judgment** | Everything else | Comparing samples, reading individual issues, noticing reporter-level patterns, writing the actual voice |

---

## The weekly workflow

### 1. Pull (automated, ~5 min)
Claude Code notebook fetches the latest 1,000 issues from `anthropics/claude-code` via the GitHub API. Enriches each with:
- Priority (P0–P3, mapped from labels)
- Area (TUI, MCP, IDE, Cowork, etc.)
- Type flags (bug / enhancement / regression / question)
- `has_repro` (whether reproduction steps are present)
- Engagement (comments, reactions — voice of customer signal)
- Aging (created / updated timestamps)
- Reporter handle (used in step 5)

Output: `triage_tracker.xlsx`, ready for analysis.

### 2. Classify (semi-automated, ~10 min)
Claude Code adds yes/no columns for the four type categories. I spot-check ~20 random rows and any Claude flagged as low-confidence. Disagreements get logged and feed the next prompt iteration.

**Coverage metric I track:** % of issues with all four type flags assigned. Currently ~89% (110 untyped in the last run). Target: 95%+.

### 3. Cluster (Claude Chat, ~15 min)
I drop the .xlsx into the project and ask for theme clustering — typically 5–7 themes with counts. I compare against last week's themes:
- Same themes, similar volumes → status quo, brief mention
- Theme volume jumps >20% → flag in the memo
- New theme appears → investigate before reporting

### 4. Sample-read (manual, ~30 min)
I read 10–15 actual issues across the top themes. Two reasons: calibrate Claude's classification, and pick up the qualitative texture (frustration language, repro quality, version-string patterns). This is where the regression insight came from — pattern-matching "this used to work in 2.1.128" across multiple tickets.

### 5. Reporter scan (Claude Code, ~10 min)
Top 10 reporters by issue volume in the cut, ranked alongside GitHub follower / activity signal. Flags individuals worth a closer look — high-volume reporters often fall into one of three buckets:

- **Power users** — file detailed issues with clean repros; worth direct CS engagement
- **Churning users** — frustration patterns escalating over time; worth proactive outreach before they leave
- **Triage anomalies** — one user hitting many surfaces may signal a workflow pattern engineering should know about

This step exists because aggregate analysis surfaces themes; individual reporter patterns surface operational stories. Both matter; the second one is harder to automate well.

### 6. Draft (Claude Chat → manual rewrite, ~30 min)
Claude Chat generates a first-pass memo using a stored prompt that includes audience profile, last week's memo for tone consistency, and the new data. I rewrite in my voice — Claude's draft tends toward AI-generated cadence (parallel structures, hedging, over-explanation). Final memo is structurally Claude's; voice is mine.

### 7. Critic pass (Claude Chat, ~10 min)
I prompt Claude to grade the memo as the recipient (Claude Code PMs in this case; for other audiences, the audience profile changes). Grades come back as 1–10 scores against four dimensions plus written feedback. I take what's useful, ignore what isn't, ship.

### 8. Ship (~5 min)
Memo goes out. I save the .xlsx and the memo to the repo with a date stamp. Diff against prior weeks is now part of next week's input.

---

## What stays human

- **Severity calls on edge cases.** Claude is good at applying labels; humans are still better at "is this actually a P0 or just an angry user."
- **Customer-specific signal.** Anything tied to a known account, a specific contract, or a procurement conversation — needs human + CS input, not just GitHub data.
- **Framing.** What this means *for the reader* is judgment. Claude doesn't know which insight is going to land in the room.
- **Voice.** The memo has to sound like a colleague, not a system. Claude drafts; I rewrite.
- **Reporter-level operational stories.** Aggregate analysis tells you what's broken; reading individual reporters tells you who's frustrated and what to do about it. Recommending CS outreach, escalating a power user to engineering, or flagging a churn risk are judgment calls.

---

## What gets faster as we run it more

- **Classification accuracy.** Disagreement log feeds prompt updates. Untyped rate should trend down each week.
- **Theme stability.** Once the taxonomy stabilizes, week-over-week diffs become the primary unit of analysis, not raw counts.
- **Critic prompt.** Audience-grading gets sharper as I tune it against actual reader feedback.
- **Reporter detection.** Right now this is a one-off Claude Code script per week; could be a standing dashboard with rolling-window volume thresholds.

---

## What this would look like as a productized program

Same pipeline, more automation around it:

- Nightly classification run instead of weekly batch
- Cluster-alert thresholds (3+ similar issues in 7 days → flag automatically)
- Auto-drafted issue acknowledgments for the on-call PM to review in batch
- Themes dashboard everyone reads, replacing some of the memo's job
- Release-aligned changelog draft, generated from resolved-issue diff
- Reporter-pattern alerts (any user crossing N issues in a 30-day window → notify CS)

The current workflow is the lightweight version. The productized version is the same shape with more automation and less manual stitching — a reasonable next step once the underlying signal is trusted.

---

## A note on tradeoffs

I considered building a single end-to-end pipeline that did the whole analysis in one prompt. Decided against it for now, for two reasons:

1. **Spot-checking matters more than throughput.** Every step where I read actual issues caught something the aggregate missed. Automating the read-loop too aggressively would lose the reporter-pattern signal and the version-string regression insight.
2. **The judgment layer needs to stay close to the data.** If I'm only reading Claude's summary, I'm not really doing product ops — I'm reviewing reports. The point is to catch what the model misses, which means I have to be in the data.

The right balance is automation for the mechanical work and friction-by-design for the judgment work. That's how this version is built.

— Kelly
