# `reflect` skill — design spec

**Date:** 2026-07-09
**Status:** Approved (brainstorming), pending implementation plan
**Repo:** `workflow-daily-work` -> `plugins/dev-workflows/skills/reflect/`

## Purpose

A session retrospective that converts **this session's problems into durable improvements**, each routed to wherever it will actually fire next time. The goal is compounding efficiency: every session should make the next one measurably better by feeding a lesson back into the workflow system (skills), the project rules (CLAUDE.md), or persistent memory.

It is deliberately **problem-focused**, not a session summary. Session summaries are already covered by `invoice-generator` (what was done, from git). `reflect` captures the *delta*: what went wrong, what was slow, what got corrected, and what should change so it doesn't recur.

## When to invoke

- `/reflect` directly, at any point (especially after a painful debugging round, mid-session).
- Phrases: "what did we learn", "retro", "retrospective", "improve our workflow", "how do we not repeat this".
- Offered automatically by the `daily` skill's **WRAP** station: after `invoice-generator` + the end-of-day snapshot, WRAP asks *"Harvest lessons from today with /reflect? (y/n)"*. This completes the daily arc: start -> work -> file -> report -> wrap -> **learn**.

## When NOT to invoke

- **Trivial or purely conversational sessions** — nothing durable to harvest. The skill is allowed to conclude "no lesson" and exit; that is a first-class, valid outcome.
- As a substitute for `post-mortem` (canonical record of one fixed bug) or `invoice-generator` (what-was-done summary). `reflect` sits above both: it asks *what should change about how we work*, not *what did we do*.

## Scope of analysis (v1)

Analyze the **current conversation context**. v1 does **not** parse transcript files on disk. If the session was compacted, work from what remains in context and say so explicitly in the output ("analysis limited to post-compaction context"). Parsing raw transcripts is a possible v2 extension, out of scope here.

## Write authority

**Apply-after-approval.** The skill analyzes, presents findings as a numbered list with concrete proposed changes, the user picks which to act on, and the skill then *actually applies* the approved ones (edits skill source, writes memory, edits CLAUDE.md, or hands off to skill-creator). Proposals never applied are the write-only-journal failure mode this skill exists to avoid; the user is solo, so there is no second person to hand a report to.

Every apply ends with the **commit offer** (never auto-commit), matching the `daily` skill's pattern.

## Stages

### Stage 1 — Harvest

Scan the session for four signal types:

| Signal | Definition |
|---|---|
| **Correction** | The user corrected the approach, output, or understanding. |
| **Friction** | Repeated manual steps, wrong tool tried first, retries, permission churn, slow paths. |
| **Skill failure** | A skill was used but its guidance was wrong/insufficient, OR a skill should have triggered and didn't. |
| **Skill gap** | A recurring workflow done ad-hoc that no skill covers. |

Each finding records: **what happened**, **evidence** (a concrete moment from the session), **cost** (rework / time / tokens), and the **proposed lesson**.

Cap at **~5 findings**, ranked by cost. This is a high-signal harvest, not an exhaustive audit. If nothing clears the bar, say so and exit.

### Stage 2 — Research & route

Before proposing anything, each finding passes through up to three research passes, **gated by finding type** so tokens aren't spent on searches a finding doesn't warrant.

**Pass A — Local overlap (always).** Search owned skills, the auto-memory index (`MEMORY.md`), and the relevant project `CLAUDE.md` for existing coverage. *Update beats create.*

**Pass B — External prior art (only for Route B "new skill" candidates).** Before proposing a brand-new skill, search:
- **GitHub** via `gh search repos` / `gh search code` — existing Claude skills, `SKILL.md` patterns, awesome-claude-code-style lists, superpowers-derived skills.
- **Web** via WebSearch/WebFetch — the workflow pattern in general.

Outcome is one of: **adopt** (a good skill already exists — reference/adapt instead of writing from scratch), **inform** (patterns worth borrowing), or **greenfield** (nothing good — build it). This applies "update beats create" at the ecosystem level, not just locally.

**Pass C — Technical verification (only when the lesson is a technical claim).** Verify against authoritative sources before persisting: official docs (Microsoft Learn / MDN / etc.), the actual code, and relevant GitHub issues/discussions. Never persist a wrong "fix" forever.

**Guardrails on external research:**
- **Read-only input to proposals** — external findings inform suggestions; nothing external is auto-applied or copied wholesale into a skill without the user seeing it in Stage 3.
- **Bounded** — a couple of targeted searches per qualifying finding, not an open-ended crawl. Inconclusive searches yield "no strong prior art found" and the finding proceeds; research never blocks.
- **Attributed** — proposals that borrow from an external source cite the URL/repo in Stage 3 and in the reflection log, so the user can judge source quality and licensing before adopting.

**Routing table** — after research, each finding is assigned exactly one destination:

| Route | Destination | When |
|---|---|---|
| A | **Update existing skill** | An owned skill should have prevented this. |
| B | **New skill** (hand off to `skill-creator`) | Recurring workflow, no skill covers it, no good external skill to adopt. |
| C | **Project `CLAUDE.md`** | Project-specific convention or gotcha. |
| D | **Auto-memory** | Preference or single-project fact. |
| E | **Discard** | One-off noise — a valid outcome. |

**Ownership guardrail:** Route A applies only to skills the user **owns** — any plugin in this repo (`dev-workflows`, `ado-backlog`, `github-backlog`, ...) and personal skills under `~/.claude/skills`. Third-party skills (superpowers, skill-creator, Microsoft plugins) are **read-only**; lessons about them become a Route D memory or a Route C CLAUDE.md override instead of an edit to the third-party skill.

### Stage 3 — Present & approve

Present a numbered list. Each item shows: **finding -> evidence -> route -> concrete proposed change** (actual replacement text or a diff, plus any cited external source — never "improve X"). The user replies with which numbers to apply (all / some / none).

### Stage 4 — Apply (only approved items)

Per route:

- **Route A (update owned skill):**
  1. Edit the skill **source**, **never** the installed plugin cache. For a plugin in this repo, edit under `C:\Repo2\workflow daily work`; for a personal skill, edit under `~/.claude/skills`.
  2. If the skill is a plugin in this repo, bump the **owning** plugin's `version` in BOTH its own `plugins/<plugin>/.claude-plugin/plugin.json` and its entry in the repo-root `.claude-plugin/marketplace.json` (keep identical). A personal `~/.claude/skills` skill has no manifest/version to bump.
  3. The running plugin is a **snapshot copied at install time**, so the edit does not take effect until the cache is re-synced. `/plugin` is gated in this environment, so re-sync is manual: re-copy the plugin into the cache version dir, update `version` + `gitCommitSha` + `lastUpdated` in `~/.claude/plugins/installed_plugins.json`, then **restart Claude Code**. The skill performs the file-level steps it can and then **tells the user a restart is required** for the change to load (it cannot restart the session itself). Reference procedure: the `claude-skills-resync-mechanism` memory.
- **Route B (new skill):** hand off to `skill-creator` / `writing-skills` with the harvested requirement — do not hand-roll a `SKILL.md` that duplicates that skill's job.
- **Route C (CLAUDE.md):** edit the relevant repo's `CLAUDE.md`, following its existing structure.
- **Route D (memory):** write the memory file into the auto-memory dir and add a one-line pointer to `MEMORY.md`, per the memory schema (check for an existing file to update before creating a duplicate).
- **Route E:** nothing.

### Stage 5 — Record & commit offer

- Append a terse block to `docs/reflections/YYYY-MM.md` in the plugin repo (one file per month; create the `docs/reflections/` dir on first use). One block per session: **date, project, findings (one line each), applied vs. skipped, cited sources**. This is the audit trail — short, greppable, not a narrative.
- Run the **commit offer** (assisted, never automatic), mirroring `daily`: write files first, then explicitly ask before staging/committing. Respect the workspace git rules — confirm the target repo before committing when the path is a non-repo root or one of several sub-repos.

## Decisions (locked during brainstorming)

1. **Reflection log lives centrally** in the plugin repo (`docs/reflections/`), not per-project — the skill improves the *workflow system*, so its trail belongs with the system.
2. **Monthly log file** rather than per-session files — keeps the folder from sprawling; entries are short.
3. **Apply-after-approval** write authority (not propose-only) — the user is solo; unapplied proposals rot.
4. **v1 reads current context only** — no transcript-file parsing.

## Out of scope (v1)

- Parsing raw transcript files from disk (possible v2).
- Auto-restarting Claude Code to load a re-synced plugin (harness limitation — user does the restart).
- Editing third-party skills.
- Cross-session trend analysis (aggregating many reflections to find systemic patterns) — the monthly log makes this possible later, but the skill does not do it in v1.

## Files touched by implementation

- **New:** `plugins/dev-workflows/skills/reflect/SKILL.md`
- **Edit:** `plugins/dev-workflows/skills/daily/SKILL.md` (WRAP station — add the `/reflect` offer)
- **Edit:** `plugins/dev-workflows/.claude-plugin/plugin.json` (register skill, description, keywords, version bump)
- **New (runtime):** `docs/reflections/` (created on first reflection)
