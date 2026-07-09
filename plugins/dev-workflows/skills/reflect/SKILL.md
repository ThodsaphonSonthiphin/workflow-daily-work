---
name: reflect
description: >-
  Session retrospective that turns THIS session's problems into durable,
  correctly-routed improvements. Trigger on /reflect, "what did we learn",
  "retro", "retrospective", "improve our workflow", "how do we not repeat
  this", or after a painful debugging round. It captures the DELTA (what
  went wrong, what was slow, what got corrected) and routes each lesson to
  where it will fire again: an owned skill, a project CLAUDE.md, or memory.
  NOT a what-was-done summary (that is invoice-generator) and NOT a single
  bug's root-cause record (that is post-mortem).
---

# reflect — turn this session's problems into durable improvements

Every session teaches something. This skill harvests those lessons and files
each one where it will actually fire next time, so the workflow compounds.

It is **problem-focused**, not a summary. If you want "what did I do", that is
`invoice-generator`. If you want one bug's canonical record, that is
`post-mortem`. `reflect` asks: **what should change about how we work?**

## When NOT to run

- Trivial or purely conversational sessions — concluding "no durable lesson"
  and exiting is a valid, first-class outcome. Do not manufacture findings.
- As a stand-in for `invoice-generator` or `post-mortem`.

## Scope

Analyze the **current conversation context**. Do NOT parse transcript files
from disk. If the session was compacted, work from what remains and say so:
"analysis limited to post-compaction context".

## Stage 1 — Harvest

Scan the session for four signal types:

| Signal | Definition |
|---|---|
| Correction | The user corrected the approach, output, or understanding. |
| Friction | Repeated manual steps, wrong tool first, retries, permission churn. |
| Skill failure | A skill was used but guided wrong/insufficiently, OR should have triggered and did not. |
| Skill gap | A recurring workflow done ad-hoc that no skill covers. |

For each finding record: **what happened**, **evidence** (a concrete moment),
**cost** (rework / time / tokens), **proposed lesson**.

Cap at ~5 findings, ranked by cost. High-signal, not exhaustive. If nothing
clears the bar, say so and exit.

## Stage 2 — Research & route

Per finding, run up to three passes, gated by type so tokens are not wasted:

- **Pass A — Local overlap (always).** Search owned skills, the auto-memory
  index (MEMORY.md), and the relevant project CLAUDE.md. Update beats create.
- **Pass B — External prior art (only for new-skill candidates).** Search
  GitHub (`gh search repos` / `gh search code`) for existing Claude skills and
  SKILL.md patterns, and the web (WebSearch/WebFetch) for the pattern. Outcome:
  adopt (good skill exists — reference it), inform (borrow patterns), or
  greenfield (build it).
- **Pass C — Technical verification (only when the lesson is a technical
  claim).** Verify against official docs, the actual code, and GitHub
  issues before persisting. Never persist a wrong fix forever.

Research guardrails: external findings are read-only input to proposals
(nothing auto-applied); bounded to a couple of targeted searches per finding
(inconclusive -> "no strong prior art found", proceed, never block); attribute
any borrowed source by URL/repo.

Assign each finding exactly one route:

| Route | Destination | When |
|---|---|---|
| A | Update existing skill | An owned skill should have prevented this. |
| B | New skill (hand to skill-creator) | Recurring workflow, no skill, no good external one to adopt. |
| C | Project CLAUDE.md | Project-specific convention or gotcha. |
| D | Auto-memory | Preference or single-project fact. |
| E | Discard | One-off noise. |

**Ownership guardrail:** Route A applies ONLY to owned skills — `dev-workflows`,
`ado-backlog`, `~/.claude/skills`. Third-party skills (superpowers,
skill-creator, Microsoft plugins) are READ-ONLY; their lessons become a Route D
memory or a Route C CLAUDE.md override instead.

## Stage 3 — Present & approve

Present a numbered list. Each item: **finding -> evidence -> route -> concrete
proposed change** (actual replacement text or diff, plus any cited source —
never "improve X"). The user replies which numbers to apply (all / some / none).

## Stage 4 — Apply (approved items only)

- **Route A (owned skill):** edit the skill SOURCE at `C:\Repo2\workflow daily
  work` (never the installed cache); bump the plugin version in BOTH
  `plugins/dev-workflows/.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json`. The edit will not load until the cache is
  re-synced and Claude Code restarts — perform the file steps, then TELL the
  user a restart is required (you cannot restart the session). See the
  `claude-skills-resync-mechanism` memory for the copy + installed_plugins.json
  procedure.
- **Route B (new skill):** hand off to `skill-creator` / `writing-skills` — do
  not hand-roll a SKILL.md that duplicates their job.
- **Route C (CLAUDE.md):** edit the relevant repo's CLAUDE.md, matching its
  structure.
- **Route D (memory):** write the memory file and add a one-line MEMORY.md
  pointer, per the memory schema; check for an existing file to update first.
- **Route E:** nothing.

Note: writes into `C:\Repo2\workflow daily work` and other non-glasshull paths
are blocked for the Write/Edit tools by the mobile-app write-guard hook — use
PowerShell here-strings or Bash for those.

## Stage 5 — Record & commit offer

- Append a terse block to `docs/reflections/YYYY-MM.md` in the plugin repo
  (create `docs/reflections/` on first use). One block per session: date,
  project, findings (one line each), applied vs skipped, cited sources.
  Short and greppable — not a narrative.
- Run the commit offer (assisted, never automatic): write files first, then ask
  before staging/committing. Respect workspace git rules — confirm the target
  repo before committing when the path is a non-repo root or one of several
  sub-repos.
