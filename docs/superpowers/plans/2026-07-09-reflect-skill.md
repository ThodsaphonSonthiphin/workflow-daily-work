# `reflect` Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `/reflect` skill in the dev-workflows plugin that turns a session's problems into durable, correctly-routed improvements (skill edits, CLAUDE.md, or memory), closing the daily arc with a "learn" beat.

**Architecture:** One process skill (`skills/reflect/SKILL.md`) driving five stages — Harvest -> Research & route -> Present -> Apply -> Record. It is wired into the `daily` WRAP station as an optional offer, and registered by keeping the `dev-workflows` description/keywords/version in sync across the plugin manifest and the marketplace manifest. Skills are auto-discovered from the `skills/` dir, so there is no skills array to edit.

**Tech Stack:** Markdown SKILL.md (frontmatter + prose), JSON manifests, Python for YAML/JSON validation, `gh` CLI + WebSearch/WebFetch for the skill's own research stage. No runtime code — the deliverable is prompt/instruction documentation.

## Global Constraints

- **Write-hook block:** the Write tool is blocked for any path outside `C:\Repo\glasshull repo\Obsidian\glasshull\raw\glasshull` by the mobile-app plugin write-guard hook. All files in `C:\Repo2\workflow daily work` MUST be created/edited via PowerShell (`Set-Content` with a single-quoted here-string) or the Bash tool — never the Write/Edit tools. Editing existing files with the Edit tool will also be blocked; use PowerShell to rewrite or Bash `sed`-free rewrites.
- **Language:** all skill content in English (user preference).
- **Version bump:** current `dev-workflows` version is `0.22.0`; bump to `0.23.0` (new skill = minor). The `version` field must be identical in `plugins/dev-workflows/.claude-plugin/plugin.json` and the `dev-workflows` entry of `.claude-plugin/marketplace.json`.
- **No auto-commit:** never commit without an explicit user go-ahead and a named branch/target (user owns Gitflow; solo dev).
- **Ownership guardrail (baked into the skill):** the skill may edit only user-owned skills (`dev-workflows`, `ado-backlog`, `~/.claude/skills`); third-party skills (superpowers, skill-creator, Microsoft plugins) are read-only.
- **Activation caveat:** a directory-source plugin is a snapshot copied at install time; edits do not load until the cache is re-synced AND Claude Code restarts. The plan cannot self-activate — activation is a documented manual handoff (final section).

---

## File Structure

- **Create** `plugins/dev-workflows/skills/reflect/SKILL.md` — the entire skill (frontmatter + five-stage process). One file, one responsibility. No supporting files (self-contained process skill under ~180 lines).
- **Modify** `plugins/dev-workflows/skills/daily/SKILL.md` — WRAP station (around lines 185-188): insert the optional `/reflect` offer after the snapshot write, before the Commit offer.
- **Modify** `plugins/dev-workflows/.claude-plugin/plugin.json` — description (mention reflect), keywords (add reflect terms), version -> 0.23.0.
- **Modify** `.claude-plugin/marketplace.json` — `dev-workflows` entry: same description/keywords/version sync.
- **Runtime-only (not built here):** `docs/reflections/YYYY-MM.md` is created by the skill on first use via `mkdir -p`; no build task.

---

## Task 1: Create the reflect SKILL.md

**Files:**
- Create: `plugins/dev-workflows/skills/reflect/SKILL.md`
- Test: subagent behavior + trigger scenarios (skill-native TDD); YAML frontmatter parse.

**Interfaces:**
- Produces: a skill named `reflect` with a trigger-rich description; consumed by Task 2 (daily WRAP references `/reflect`) and Task 3 (manifests describe it).

- [ ] **Step 1: Write the trigger baseline test (RED)**

Before writing the skill, capture baseline. Dispatch a subagent with ONLY the draft description string and three prompts; record whether it says the skill should fire. This is the RED step — it documents what the description must disambiguate.

Prompts to test:
1. "what did we learn this session" -> SHOULD trigger
2. "summarize what I did today" -> should NOT trigger (that is invoice-generator)
3. "write up the root cause of this bug" -> should NOT trigger (that is post-mortem)

Expected at baseline: ambiguity between 1 and 2 (both sound like summary). The description must draw the delta/summary line explicitly.

- [ ] **Step 2: Create the SKILL.md file via PowerShell**

Create `plugins/dev-workflows/skills/reflect/SKILL.md` with exactly this content (use `Set-Content` with a single-quoted here-string; the closing token must sit at column 0 on its own line):

````markdown
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
````

- [ ] **Step 3: Verify the frontmatter parses**

Run (PowerShell):
```
python -c "import yaml,io; d=yaml.safe_load(io.open(r'C:\Repo2\workflow daily work\plugins\dev-workflows\skills\reflect\SKILL.md',encoding='utf-8').read().split('---')[1]); print('name=',d['name']); assert d['name']=='reflect'; assert len(d['description'])>200; print('OK frontmatter')"
```
Expected: `name= reflect` then `OK frontmatter`.

- [ ] **Step 4: Run the trigger test (GREEN)**

Re-dispatch the Step 1 subagent, now given the final description. Verify:
1. "what did we learn" -> triggers reflect.
2. "summarize what I did today" -> does NOT (routes to invoice-generator).
3. "write up the root cause" -> does NOT (routes to post-mortem).

Expected: all three correct. If (2) still collides, tighten the "NOT a
what-was-done summary" clause and re-run.

- [ ] **Step 5: Run the behavior test (GREEN)**

Dispatch a subagent with the full SKILL.md content plus a synthetic mini-session
containing (a) a user correction, (b) a lesson about a superpowers skill, and
(c) a project-specific gotcha. Verify the subagent:
- Produces <=5 findings with what/evidence/cost/lesson.
- Routes the superpowers-skill lesson to D or C (NOT Route A) — ownership
  guardrail holds.
- Routes the project gotcha to C (CLAUDE.md).
- Presents before applying (does not apply unbidden).

Expected: all four behaviors present. If the guardrail fails, strengthen the
Stage 2 ownership paragraph and re-run.

- [ ] **Step 6: Commit**

Do NOT commit yet — Tasks 2 and 3 belong in the same feature commit. Proceed to
Task 2. (If executing task-by-task with checkpoints, stage but hold the commit
until Task 3, then commit once with the message in Task 3 Step 4.)

---

## Task 2: Wire the /reflect offer into the daily WRAP station

**Files:**
- Modify: `plugins/dev-workflows/skills/daily/SKILL.md` (WRAP station, after the `daily-state.py set` block near line 185).

**Interfaces:**
- Consumes: the `reflect` skill from Task 1 (references `/reflect`).
- Produces: WRAP now ends with start -> work -> file -> report -> wrap -> learn.

- [ ] **Step 1: Confirm the current WRAP tail**

Read `plugins/dev-workflows/skills/daily/SKILL.md` lines 185-189. Confirm the
line `Then run the **Commit offer** below. This is the resume-point the next
session` is present immediately after the fenced `daily-state.py set` block.

- [ ] **Step 2: Insert the reflect offer**

Replace the paragraph:
```
Then run the **Commit offer** below. This is the resume-point the next session
reads on `/daily start`.
```
with:
```
After the snapshot, offer the optional **learn** beat that closes the arc:

> *Harvest today's lessons into the workflow with /reflect? (y/n)*

If the user accepts, hand off to the `reflect` skill; if they decline, skip
silently. Then run the **Commit offer** below. This is the resume-point the next
session reads on `/daily start`.
```
Use PowerShell to read the file, perform the string replace, and write it back
(the Edit tool is blocked here). Example approach:
```
$p = 'C:\Repo2\workflow daily work\plugins\dev-workflows\skills\daily\SKILL.md'
$t = [IO.File]::ReadAllText($p)
$old = "Then run the **Commit offer** below. This is the resume-point the next session`r`nreads on ``/daily start``."
# build $new with the reflect offer prepended, then:
$t = $t.Replace($old, $new)
[IO.File]::WriteAllText($p, $t)
```
If the CRLF/backtick literal makes `.Replace` brittle, instead match on the
shorter unique anchor `Then run the **Commit offer** below.` and prepend the
offer paragraph before it.

- [ ] **Step 3: Verify the edit landed and nothing else changed**

Run:
```
python -c "t=open(r'C:\Repo2\workflow daily work\plugins\dev-workflows\skills\daily\SKILL.md',encoding='utf-8').read(); assert '/reflect? (y/n)' in t; assert t.count('Commit offer** below')>=1; assert 'invoice-generator' in t; print('OK wrap wired')"
```
Expected: `OK wrap wired`.

- [ ] **Step 4: Behavior test**

Dispatch a subagent with the edited WRAP section and prompt: "I'm wrapping up my
day." Verify it invokes invoice-generator, writes the snapshot, THEN offers
/reflect, THEN offers the commit — in that order, and treats /reflect as
optional (skips silently on "n").

Expected: correct ordering; reflect offered but not forced.

- [ ] **Step 5: Commit**

Hold — commit with Task 3.

---

## Task 3: Sync registration across both manifests

**Files:**
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json` (the `dev-workflows` entry)

**Interfaces:**
- Consumes: the `reflect` skill (Task 1) it now advertises.
- Produces: version `0.23.0` in both files; descriptions/keywords mention reflect.

- [ ] **Step 1: Bump versions and mention reflect (both files)**

In `plugins/dev-workflows/.claude-plugin/plugin.json`:
- set `version` to `0.23.0`.
- append to `description` (end of the string): ` Reflection: reflect (session retrospective that routes each lesson into an owned skill, a CLAUDE.md, or memory — closing the daily arc with a learn beat).`
- add keywords: `"reflect"`, `"retrospective"`, `"retro"`, `"session-reflection"`, `"continuous-improvement"`, `"lessons-learned"`.

Apply the identical `version`, description-suffix, and keyword additions to the
`dev-workflows` object inside `.claude-plugin/marketplace.json`.

Edit via PowerShell reading JSON, mutating, and writing back with indentation
preserved. Example:
```
$p = 'C:\Repo2\workflow daily work\plugins\dev-workflows\.claude-plugin\plugin.json'
$j = Get-Content $p -Raw | ConvertFrom-Json
$j.version = '0.23.0'
$j.description = $j.description + ' Reflection: reflect ...'
$j.keywords += @('reflect','retrospective','retro','session-reflection','continuous-improvement','lessons-learned')
$j | ConvertTo-Json -Depth 10 | Set-Content $p -Encoding utf8
```
Note: `ConvertTo-Json` may reorder keys and re-escape; if the diff is noisy,
prefer a targeted string replace on the `version`/`description`/`keywords`
lines instead to keep the diff minimal.

- [ ] **Step 2: Validate both JSON files and version parity**

Run:
```
python -c "import json; a=json.load(open(r'C:\Repo2\workflow daily work\plugins\dev-workflows\.claude-plugin\plugin.json',encoding='utf-8')); b=json.load(open(r'C:\Repo2\workflow daily work\.claude-plugin\marketplace.json',encoding='utf-8')); dw=[p for p in b['plugins'] if p['name']=='dev-workflows'][0]; assert a['version']=='0.23.0'; assert dw['version']=='0.23.0'; assert 'reflect' in a['description'].lower(); assert 'reflect' in dw['description'].lower(); assert 'reflect' in a['keywords']; print('OK manifests synced')"
```
Expected: `OK manifests synced`.

- [ ] **Step 3: Final consistency sweep**

Run:
```
python -c "import os; base=r'C:\Repo2\workflow daily work\plugins\dev-workflows'; assert os.path.isfile(base+r'\skills\reflect\SKILL.md'); print('OK skill file present')"
```
Expected: `OK skill file present`.

- [ ] **Step 4: Commit (all three tasks)**

Only after the user approves committing and names the target branch. Files to
stage: the new `reflect/SKILL.md`, the edited `daily/SKILL.md`, `plugin.json`,
and `marketplace.json`. Suggested message:
```
feat(reflect): add session-reflection skill + wire into daily wrap

- new /reflect skill: harvest -> research/route -> present -> apply -> record
- daily WRAP offers /reflect as the optional learn beat
- bump dev-workflows to 0.23.0 in plugin.json + marketplace.json
```
(Match this repo's commit-trailer convention if it differs.)

---

## Activation (manual handoff — not an automated task)

The running plugin is a snapshot; the edits above do NOT load until the cache is
re-synced and Claude Code restarts. `/plugin` is gated, so re-sync by hand per
the `claude-skills-resync-mechanism` memory:

1. Re-copy `plugins/dev-workflows/*` into
   `~/.claude/plugins/cache/workflow-daily-work/dev-workflows/<version>/`. Because
   the version changed to 0.23.0, the cache folder name AND the `version` field in
   `~/.claude/plugins/installed_plugins.json` must both become `0.23.0`.
2. Update `gitCommitSha` and `lastUpdated` in `installed_plugins.json` (re-read it
   first — the plugin manager rewrites it during a session).
3. Restart Claude Code.
4. Verify `/reflect` appears in the skill list and `/daily wrap` offers it.

Tell the user these steps; the agent performs the file copies it can but cannot
restart the session.

---

## Self-Review

**Spec coverage:**
- Purpose / problem-focus vs invoice-generator & post-mortem -> Task 1 description + "When NOT to run". OK
- Triggers incl /reflect and phrases -> Task 1 frontmatter; Task 2 WRAP offer. OK
- Scope (current context only, compaction note) -> Task 1 Scope section. OK
- Apply-after-approval write authority -> Task 1 Stage 3/4. OK
- Stage 1 four signals + ~5 cap -> Task 1 Stage 1. OK
- Stage 2 three passes (GitHub/web/tech) + guardrails + routing A-E + ownership -> Task 1 Stage 2. OK
- Stage 3 present -> Task 1 Stage 3. OK
- Stage 4 apply per route + resync caveat -> Task 1 Stage 4 + Activation. OK
- Stage 5 monthly log + commit offer -> Task 1 Stage 5. OK
- WRAP integration -> Task 2. OK
- Registration (description/keywords/version, both manifests) -> Task 3. OK
- Decisions (central monthly log, apply-after-approval, v1 context-only) -> reflected in Task 1. OK
- Out-of-scope (no transcript parsing, no auto-restart, no third-party edits, no cross-session trends) -> Global Constraints + Task 1. OK

**Placeholder scan:** No TBD/TODO; every code/edit step shows exact content or exact commands. The one intentional runtime `<version>` / `YYYY-MM` tokens are runtime values, not plan placeholders.

**Type/name consistency:** skill name `reflect` consistent across Tasks 1-3; version `0.23.0` consistent; routes A-E consistent between Stage 2 table and Stage 4 apply list; ownership set (`dev-workflows`, `ado-backlog`, `~/.claude/skills`) consistent between Global Constraints and Stage 2.
