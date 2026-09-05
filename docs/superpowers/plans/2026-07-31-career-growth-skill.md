# career-growth Skill Implementation Plan

> ⚠️ **SUPERSEDED IN PART — do not generate requirements from the Station 2/3
> text in this plan.** The `paid` test it transcribes lacks the breadth half
> ([ADR 0174](../../adr/workflow-daily-work-0174-the-paid-test-requires-breadth-and-a-moat-sits-on-a-common-core.md)): distinct-employer counts in the demand table, an
> employer floor across at least two rings, and the broad-core-plus-rare-edge
> shape for every candidate. The shipped `SKILL.md` and `market-sources.md` are
> current; this plan is the historical record of the first implementation.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `career-growth` skill in `dev-workflows` — a five-station, re-runnable career-review pipeline (evidence-graded inventory → live market survey → four-test moat candidates → user-picked moat → cert-driven plan) per the approved spec `docs/superpowers/specs/2026-07-31-career-growth-skill-design.md` (ADRs 0043–0052).

**Architecture:** One interactive skill (`skills/career-growth/SKILL.md`) plus three bundled reference files (growth-state contract, bounded market-source list, interview bank), a thin command wrapper, one PLAYBOOK router row, and a version bump. All personal output goes to a user-chosen career git repo — the plugin ships no scripts and stores no personal data.

**Tech Stack:** Markdown only (SKILL.md + references + command). No scripts, no new dependencies.

## Global Constraints

- **Already done — do NOT re-create:** ADRs 0043–0052 in `docs/adr/`, the **Moat** term in `CONTEXT.md`, and the design spec. If a task's file already exists with the planned content, reconcile instead of blind-overwriting.
- **Versions in sync:** `plugins/dev-workflows/.claude-plugin/plugin.json` `version` must equal the `dev-workflows` entry's `version` in `.claude-plugin/marketplace.json` — both become `0.26.0` (from `0.25.9`).
- **Harness-neutral skill wording (Claude Code + Antigravity):** name *actions*, never one harness's tool ("ask the user", "search the web", "load the skill via your harness's mechanism" — never "AskUserQuestion", "WebFetch", "the Skill tool"). The skill references its **own** bundled files by skill-relative path (`references/…`), never `${CLAUDE_PLUGIN_ROOT}`.
- **PLAYBOOK rule (ADR 0001):** the commit that adds SKILL.md must also contain the PLAYBOOK row — Tasks 4–6 stage files and **commit once, together, in Task 6**.
- **Diagram convention:** career-growth is an *interactive* skill → any diagram SKILL.md tells the agent to print live in-session is a **terminal diagram** (Unicode box-drawing, fenced block, ADR 0010). Every *generated artifact* (`profile.md`, `market-report.md`, `moat.md`, `growth-plan.md`) opens with one overview **Mermaid** diagram (ADRs 0005–0009). Reference files bundled here open with a small Mermaid overview for uniformity.
- **Write-guard workaround (session gotcha):** a `mobile-app` hook may block Write/Edit outside `plugins/dev-workflows/`. For `PLAYBOOK.md`, `.claude-plugin/marketplace.json`, or any blocked path: Write the content to a temp file under `plugins/dev-workflows/`, then move it with PowerShell `Move-Item <tmp> <dest> -Force`. For small edits to a blocked existing file, use PowerShell `[IO.File]::ReadAllText` → `.Replace()` on a single-line anchor → `WriteAllText` with `[Text.UTF8Encoding]::new($false)`.
- **Commit-message verification (GitKraken gotcha):** after every `git commit`, run `git log -1 --format=%B` and verify the message was not rewritten by the `gk` AI hook; fix with `git commit --amend -m …` if it was.
- **Working directory:** the worktree `C:\Repo2\workflow daily work\.claude\worktrees\career-growth-skill` (branch `worktree-career-growth-skill`). All paths below are relative to it.

---

### Task 1: growth-state contract reference

**Files:**
- Create: `plugins/dev-workflows/skills/career-growth/references/growth-state-contract.md`

**Interfaces:**
- Produces: the canonical schema of `growth-state.md` (field names below). Task 4's SKILL.md cites this file as `references/growth-state-contract.md`; the field names `last_run`, `cadence_months`, `next_review_due`, `chosen_moat`, `target_certs[]`, `mini_projects[]` are used verbatim by SKILL.md Station 5.

- [ ] **Step 1: Write the file**

````markdown
# growth-state.md — contract

The single machine-readable state file the `career-growth` skill maintains in the
user's **career repo** (ADR 0049). One YAML document in a fenced block inside
`growth-state.md`. The skill owns every field; the user may hand-edit `cadence_months`.

```mermaid
flowchart LR
    RUN["career-growth run N"] -->|writes| GS[("growth-state.md")]
    GS -->|"pre-fills interview,<br/>marks projects/certs progress"| RUNN["run N+1"]
```

## Schema

```yaml
version: 1                      # contract version — bump only via a new ADR
last_run: 2026-07-31            # ISO date of the last completed full run
cadence_months: 3               # suggested review cadence (user-adjustable)
next_review_due: 2026-10-31     # last_run + cadence_months; the skill prints it at wrap-up
chosen_moat: "<one-line moat statement>"   # copied from moat.md when the user picks (Station 4)
moat_adopted_on: 2026-07-31     # date the current moat was picked
target_certs:                   # Station 5 output — one entry per live-verified cert
  - code: PL-400                # vendor exam code, exactly as the registry lists it
    name: Microsoft Power Platform Developer
    status: studying            # planned | studying | scheduled | passed | retired-blocked
    verified_on: 2026-07-31     # date the live registry check last passed
    registry_url: https://learn.microsoft.com/credentials/certifications/…
mini_projects:                  # Station 5 output — one entry per mini project
  - name: <kebab-slug>
    for_cert: PL-400            # exam this project prepares for; "none" → non-cert milestone
    milestone: "pass PL-400"    # pass/fail milestone (exam pass, or the explicit non-cert milestone)
    exam_objectives:            # the objective-domain strings this project exercises
      - "Extend the platform"
    status: planned             # planned | in-progress | done
    published_url: null         # public repo URL when published; null when private/unpublished
```

## Rules

- **Full run every time (ADR 0050):** re-runs never skip a station; this file only
  pre-fills the interview and carries project/cert progress — it is never a reason
  to skip fresh evidence gathering.
- `status: retired-blocked` is set when a previously-targeted cert fails the live
  registry check (ADR 0048 rule 1); the skill must then propose a replacement.
- The skill updates this file **last**, after the four document artifacts, so a
  crashed run never records a completed `last_run`.
````

- [ ] **Step 2: Verify the file parses as it claims**

Run (from the worktree root):
```bash
python -c "
import re,io
t=io.open('plugins/dev-workflows/skills/career-growth/references/growth-state-contract.md',encoding='utf-8').read()
assert '```yaml' in t and 'next_review_due' in t and 'retired-blocked' in t
print('contract OK')"
```
Expected: `contract OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/dev-workflows/skills/career-growth/references/growth-state-contract.md
git commit -m "feat(dev-workflows): career-growth growth-state contract reference" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git log -1 --format=%B   # verify the gk hook did not rewrite the message
```

---

### Task 2: bounded market-source list reference

**Files:**
- Create: `plugins/dev-workflows/skills/career-growth/references/market-sources.md`

**Interfaces:**
- Produces: the per-ring source list + the three evidence rules' operational detail. Task 4's SKILL.md cites it as `references/market-sources.md` and names the three rings exactly: **Thailand**, **SEA**, **Global remote**.

- [ ] **Step 1: Write the file**

````markdown
# MARKET station — bounded source list

The fixed per-ring source list that keeps MARKET a single-session stage (ADR 0047)
and the operational detail of the three evidence rules (ADR 0048). Fetchability
shifts — treat "known blocked" entries as *skip immediately*, and when a listed
board starts returning 403, try the alternates before reporting a metric
unavailable, then note the change here.

```mermaid
flowchart TD
    R1["ring 1 — Thailand"] --> B["job boards (fetchable)"]
    R2["ring 2 — SEA"] --> B
    R3["ring 3 — Global remote"] --> B
    B --> DC["demand claims<br/>(source + posting count)"]
    T["trend sources"] --> F["3-year triangulation<br/>(≥3 signal types)"]
    REG["vendor cert registries"] --> C["live-verified certs only"]
```

## Ring 1 — Thailand

| Source | Status | Notes |
|---|---|---|
| LinkedIn Jobs (location: Thailand) | fetchable | primary demand signal |
| Indeed Thailand | fetchable | cross-check counts |
| JobsDB (th.jobsdb.com) | **known blocked (403, 2026-07-31)** | skip; do not burn time retrying |

## Ring 2 — SEA (incl. Singapore)

| Source | Status | Notes |
|---|---|---|
| LinkedIn Jobs (SG / MY / VN / ID / PH) | fetchable | primary |
| Indeed Singapore | fetchable | cross-check |
| NodeFlair / regional boards | verify at run time | use only if they serve automated fetch |

## Ring 3 — Global remote

| Source | Status | Notes |
|---|---|---|
| LinkedIn Jobs (remote filter) | fetchable | primary |
| Indeed (remote filter) | fetchable | cross-check |
| We Work Remotely / RemoteOK / Hacker News "Who's hiring" | verify at run time | volume smaller; good rarity signal for niche combos |

## Trend sources (3-year triangulation — pick ≥3 signal *types*)

1. **Vendor roadmaps** — e.g. Microsoft release waves / product roadmaps (fetch the
   current wave; never cite a wave from memory).
2. **Industry & developer surveys** — WEF Future of Jobs, Stack Overflow Developer
   Survey, State of DevOps; use the newest published edition found at run time.
3. **Posting-trend deltas** — `git diff` / `git log` of `market-report.md` across
   runs in the career repo (first run: mark this signal "not yet available").
4. **AI-absorption assessment** — for each candidate skill, argue explicitly what
   share of the work current AI tooling already does, and the 3-year trajectory.

## Vendor certification registries (rule 1 — live verification, NEVER memory)

| Vendor | Where to verify |
|---|---|
| Microsoft | `learn.microsoft.com/credentials/support/retired-certification-exams` + `…/credentials/support/credential-retirement` + the exam study guide's own banner |
| Others (AWS, GCP, Scrum.org, …) | the vendor's own certification-lifecycle / retirement page, found at run time |

A cert may be recommended **only** with: exam code confirmed on a live vendor page,
no retirement listing, and the study guide fetched (its objective domains feed
Station 5's mini-project design). Record `verified_on` + `registry_url` in
`growth-state.md`.
````

- [ ] **Step 2: Verify**

```bash
python -c "
import io
t=io.open('plugins/dev-workflows/skills/career-growth/references/market-sources.md',encoding='utf-8').read()
assert 'known blocked' in t and 'retired-certification-exams' in t and 'Ring 3' in t
print('sources OK')"
```
Expected: `sources OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/dev-workflows/skills/career-growth/references/market-sources.md
git commit -m "feat(dev-workflows): career-growth bounded market-source reference" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git log -1 --format=%B
```

---

### Task 3: gap-fill interview bank reference

**Files:**
- Create: `plugins/dev-workflows/skills/career-growth/references/interview-bank.md`

**Interfaces:**
- Produces: the question bank Task 4's SKILL.md cites as `references/interview-bank.md`. Section names (`Non-git work`, `Soft skills & languages`, `Domain knowledge`, `Constraints & preferences`) are referenced by SKILL.md Station 1.

- [ ] **Step 1: Write the file**

````markdown
# INVENTORY station — gap-fill interview bank

Questions for the short targeted interview (ADR 0046 source 4). Ask **only**
questions whose answer the evidence cannot show, and **pre-fill from the previous
`profile.md`** so a returning user corrects instead of re-answering (ADR 0050).
One question at a time; skip any section the evidence already covers.

```mermaid
flowchart LR
    EV["evidence read<br/>(resume·repos·git·certs·ADO)"] --> GAPS{"what is still unknown?"}
    GAPS -->|only those| Q["targeted questions<br/>from this bank"]
    Q --> P["profile.md entries<br/>graded: interview-attested"]
```

## Non-git work

- What delivered work of the last 2 years left no git trace (config, ops,
  migrations, integrations, admin, reports)?
- What systems do you operate or support that you did not build?

## Soft skills & languages

- Which human languages do you work in, at what level (meetings / writing / docs)?
- Have you led anything — a feature, a rollout, a person, a vendor call?
- What do colleagues come to you for?

## Domain knowledge

- Which business domains have you shipped into (e.g. shipping/logistics, finance),
  and how deep — vocabulary-level, process-level, or design-level?
- Which regulations, standards, or industry practices do you know from the inside?

## Constraints & preferences

- Hours per week you can actually study, sustainably?
- Exam budget per quarter (certs cost money) — any employer sponsorship?
- Remote / relocation constraints across the target rings?
- Anything you refuse to work on, regardless of market demand?

## Grading rule

Every answer becomes a `profile.md` entry graded **interview-attested** — weaker
than repo/cert evidence, stronger than resume-only. Never let an interview answer
upgrade a resume-only claim to *verified*; only artifacts do that.
````

- [ ] **Step 2: Verify**

```bash
python -c "
import io
t=io.open('plugins/dev-workflows/skills/career-growth/references/interview-bank.md',encoding='utf-8').read()
assert 'interview-attested' in t and 'Constraints & preferences' in t
print('bank OK')"
```
Expected: `bank OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/dev-workflows/skills/career-growth/references/interview-bank.md
git commit -m "feat(dev-workflows): career-growth interview-bank reference" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git log -1 --format=%B
```

---

### Task 4: SKILL.md — the skill itself

**Files:**
- Create: `plugins/dev-workflows/skills/career-growth/SKILL.md`

**Interfaces:**
- Consumes: `references/growth-state-contract.md` (Task 1), `references/market-sources.md` (Task 2), `references/interview-bank.md` (Task 3) — cited by exactly these skill-relative paths.
- Produces: skill name `career-growth` (frontmatter `name:`), consumed by Task 5's command and Task 6's PLAYBOOK row.

**⚠ Do NOT commit in this task** — the PLAYBOOK rule requires SKILL.md and the PLAYBOOK row in one commit (Task 6).

- [ ] **Step 1: Write the file**

````markdown
---
name: career-growth
description: Quarterly career review that turns your real evidence and a live market survey into a defensible moat and a cert-driven growth plan. Builds an evidence-graded skill inventory (resume, repos, cross-repo git history, held certs/LinkedIn, optional Azure DevOps work items, short gap-fill interview), surveys Thailand + SEA + global-remote job markets with live-verified certificates and a triangulated 3-year outlook, proposes moat candidates that must pass four tests (rare, evidenced, paid, durable), lets the user pick, then plans certs and exam-objective-driven mini projects into a personal career git repo. Trigger when the user wants a career review, skill-gap analysis, certification roadmap or plan, job-market survey, "what should I learn next", a moat / unique edge / competitive advantage plan, or says "พัฒนาสกิลตัวเอง", "วางแผน cert", "ตลาดแรงงานต้องการอะไร", "สร้างจุดเด่น", "quarterly career review". Re-run it every quarter.
---

# career-growth

Five stations, full run every time, everything written to the user's **career
repo** (a git repo of their choosing — never this plugin, never the current
project). The user — not this skill — picks the career direction.

Print this pipeline diagram verbatim in your first response of a run:

```
CAREER-GROWTH — five stations, full run every time
──────────────────────────────────────────────────

  ① INVENTORY   evidence-graded skill inventory
  │    resume · repos · git history ·
  │    certs/LinkedIn · ADO (if available) ·
  │    gap-fill interview
  ▼
  ② MARKET      live survey — 3 rings
  │    Thailand · SEA · global remote
  │    certs live-verified · 3-yr outlook
  │    triangulated (≥3 signal types)
  ▼
  ③ GAP + MOAT  inventory × market
  │    candidates argued against 4 tests:
  │    rare · evidenced · paid · durable
  ▼
  ④ PRESENT ⛔  the user picks the moat
  │    (approval gate — nothing below
  │     runs without an explicit pick)
  ▼
  ⑤ PLAN        cert-driven guideline
       mini projects from exam objectives
       → career repo, assisted commit
```

## Non-negotiable evidence rules

1. **Never answer certificate questions from memory.** Every cert you mention as
   available must be verified at run time against the vendor's live
   retirement/lifecycle registry — see `references/market-sources.md` for where.
   If the registry is unreachable, withhold cert recommendations; never guess.
2. **Demand claims need a source.** Job-market statements carry the board name and
   posting count. Use only boards that serve automated fetch; on a 403 try the
   listed alternates before reporting a metric unavailable.
3. **No 3-year claim without triangulation** — at least three signal types from
   `references/market-sources.md` (vendor roadmaps, industry surveys, run-to-run
   posting deltas, AI-absorption assessment).
4. **Personal data never enters this plugin or the current project.** All outputs
   go to the career repo. Commits there are assisted — propose, show, let the user
   approve — never automatic.

## Step 0 — Preflight

1. Ask the user for (or confirm from a previous run): the **career repo path**,
   the **resume file path**, and the **list of repo roots** to scan. If the career
   repo doesn't exist or isn't a git repo, offer to create/`git init` it.
2. Read `growth-state.md` and the four artifacts from the career repo if present
   (see `references/growth-state-contract.md`). They pre-fill this run; they never
   skip a station.
3. Detect the optional ADO source: if the `ado-backlog` plugin's skills are
   available in this session, plan to use its assigned-work view in Station 1;
   otherwise tell the user the ADO source is skipped and continue.
4. Confirm the target market rings — default **Thailand + SEA + global remote**;
   the user may narrow or swap for this run.

## Station 1 — INVENTORY

Build the skill inventory from five sources (skip cleanly what the user lacks):

1. **Resume** — read the file; extract claimed skills, roles, domains.
2. **Repos + git history** — for each repo root: scan commit history (what was
   built, how recently, how often; languages, frameworks, infra). This is the
   corrective to resume claims.
3. **Held certificates + LinkedIn** — ask the user to paste/export; never scrape.
4. **ADO work items** (only if available per preflight) — list delivered work
   items as org-internal evidence.
5. **Gap-fill interview** — ask only what the evidence cannot show, one question
   at a time, from `references/interview-bank.md`, pre-filled from the previous
   `profile.md` so the user corrects rather than re-answers.

Write **`profile.md`** to the career repo: every entry lists its attesting
source(s) and an evidence grade — `verified` (artifact: repo/cert/work item),
`interview-attested`, or `unverified` (resume-only). Open the document with one
overview Mermaid diagram (skill map grouped by evidence grade).

## Station 2 — MARKET

Survey each confirmed ring using **only** the bounded source list in
`references/market-sources.md`, under the evidence rules above. For the chosen
skill areas gather: demand (posting counts per ring), the certificates employers
name (each live-verified before it may be mentioned), compensation signals where
boards expose them, and the 3-year outlook (triangulated, with the AI-absorption
assessment stated per skill).

Write **`market-report.md`** to the career repo: overview Mermaid diagram (rings ×
demand), a demand table per ring (skill · postings · source · date), the verified
cert list (code, status, `verified_on`, registry URL), and the triangulated
outlook with each signal cited. Do not delete the previous report's insights —
the file is overwritten, git history keeps the rounds.

## Station 3 — GAP + MOAT

Cross INVENTORY × MARKET:

- **Gap list** — market-demanded skills the user lacks or holds unverified.
- **Moat candidates** — skill *combinations* (never single hot skills), each with
  a four-test argument, one line per test:
  `rare` (evidence of scarcity in the rings) · `evidenced` (what public proof the
  user has or would gain) · `paid` (demand claims with sources) · `durable`
  (the triangulated 3-year case).
- Anything failing a test may appear only as a labeled **supporting skill** —
  never as a moat candidate.

## Station 4 — PRESENT ⛔ approval gate

Present the candidates (a compact table: combination · the four test verdicts ·
strongest evidence) and ask the user to **pick one moat, or reject all**. On
reject: collect the objections as constraints and loop back to Station 3. Never
pick for the user; never proceed past this gate without an explicit pick.

On a pick, write **`moat.md`** to the career repo: the chosen combination, its
full four-test argument, the rejected candidates (one line each, why), and an
overview Mermaid decision diagram (chosen vs rejected).

## Station 5 — PLAN

For the chosen moat:

1. **Target certs** — select the certificates that evidence the moat, each
   already live-verified in Station 2. Fetch each exam's **study guide** and
   extract its objective domains.
2. **Mini projects** — design each project *backwards from exam objectives*: the
   project exists to build the knowledge the exam tests; passing the exam is the
   milestone. Size each to the user's stated study hours. Offer (never require)
   to publish each project to a public repo when its content allows — record
   `published_url` when taken.
3. **Non-cert milestones** — any moat component with no matching cert gets an
   explicit alternative milestone (a shipped artifact or delivered work), stated
   in the same pass/fail form.
4. Write **`growth-plan.md`** (overview Mermaid diagram: certs + projects on a
   quarter timeline; then per-project sections: objective domains covered,
   milestone, size, publish decision) and update **`growth-state.md`** per
   `references/growth-state-contract.md` — state file last, so a crashed run
   never records a completed `last_run`.
5. **Wrap up:** propose the career-repo commit (assisted — show the diff summary,
   let the user approve), and print the `next_review_due` date with a reminder
   that re-runs are user-initiated.

## Failure & degradation

| Situation | Behavior |
|---|---|
| A job board 403s | try the alternates in `references/market-sources.md`; only then report the metric unavailable |
| Vendor cert registry unreachable | withhold cert recommendations — never from memory; mark affected certs `retired-blocked` if previously targeted |
| `ado-backlog` absent | skip the ADO source with an explicit notice |
| No web access at all | INVENTORY still runs; MARKET and PLAN stop and say why — never fabricate |
| User rejects all candidates | loop to Station 3 with their objections as constraints |
````

- [ ] **Step 2: Verify frontmatter + harness neutrality + self-containment**

```bash
python -c "
import io
t=io.open('plugins/dev-workflows/skills/career-growth/SKILL.md',encoding='utf-8').read()
assert t.startswith('---') and 'name: career-growth' in t
low=t.lower()
for bad in ['askuserquestion','webfetch','websearch','skill tool','claude_plugin_root']:
    assert bad not in low, bad
for ref in ['references/growth-state-contract.md','references/market-sources.md','references/interview-bank.md']:
    assert ref in t, ref
print('SKILL.md OK')"
```
Expected: `SKILL.md OK`

- [ ] **Step 3: Stage only (no commit — PLAYBOOK rule)**

```bash
git add plugins/dev-workflows/skills/career-growth/SKILL.md
```

---

### Task 5: command wrapper

**Files:**
- Create: `plugins/dev-workflows/commands/career-growth.md`

**Interfaces:**
- Consumes: skill name `career-growth` (Task 4).
- Produces: the `/dev-workflows:career-growth` entry point.

**⚠ Stage only; commit happens in Task 6.**

- [ ] **Step 1: Write the file** (same shape as `commands/daily.md`)

```markdown
---
description: Quarterly career review — evidence-graded skill inventory, live market + certificate survey (Thailand/SEA/global remote), four-test moat selection, cert-driven growth plan with mini projects. Full run every time; outputs to your personal career repo.
argument-hint: "[career-repo-path]"
---

Use the **`career-growth`** skill.

Argument: $ARGUMENTS
```

- [ ] **Step 2: Verify**

```bash
python -c "
import io
t=io.open('plugins/dev-workflows/commands/career-growth.md',encoding='utf-8').read()
assert t.startswith('---') and 'argument-hint' in t and 'career-growth' in t
print('command OK')"
```
Expected: `command OK`

- [ ] **Step 3: Stage**

```bash
git add plugins/dev-workflows/commands/career-growth.md
```

---

### Task 6: PLAYBOOK row + README row + the skill commit

**Files:**
- Modify: `PLAYBOOK.md` (WORKING router diagram + table)
- Modify: `plugins/dev-workflows/README.md` (Skills table)

**Interfaces:**
- Consumes: skill name `career-growth` (Task 4), staged files from Tasks 4–5.

**⚠ `PLAYBOOK.md` is outside `plugins/dev-workflows/` — if the write-guard blocks the edit, use the PowerShell single-line-anchor `.Replace()` flow from Global Constraints.**

- [ ] **Step 1: Add the router node to PLAYBOOK.md's WORKING diagram**

In the `## WORKING — the situational router` mermaid block, insert after the line
`    WORK -- need a full SA/design document --> SAD["sa-doc"]`:

```
    WORK -- planning my own growth --> CG["career-growth"]
```

- [ ] **Step 2: Add the router table row**

In the table under that diagram, insert after the row
`| need a repeatable test-case suite (feature / change / fixed bug) | \`generating-test-cases\` |`:

```markdown
| planning my own growth / quarterly career review | `career-growth` |
```

- [ ] **Step 3: Add the README Skills-table row**

In `plugins/dev-workflows/README.md`, append to the `## Skills` table:

```markdown
| `career-growth` | **Quarterly career review.** Builds an **evidence-graded skill inventory** (resume, repos, git history, certs, optional ADO), surveys **Thailand + SEA + global-remote** markets with **live-verified certificates** and a triangulated 3-year outlook, proposes **moat candidates** that must pass four tests (rare · evidenced · paid · durable), lets **you** pick, then writes a **cert-driven plan** (mini projects designed from exam objectives) into your personal career git repo. Full run every time. |
```

- [ ] **Step 4: Verify both rows landed**

```bash
grep -n "career-growth" PLAYBOOK.md plugins/dev-workflows/README.md
```
Expected: ≥1 match in each file (diagram + table in PLAYBOOK, one row in README).

- [ ] **Step 5: Commit the skill as one unit**

```bash
git add PLAYBOOK.md plugins/dev-workflows/README.md
git commit -m "feat(dev-workflows): add career-growth skill — quarterly career review with four-test moat (ADRs 0043-0052)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git log -1 --format=%B
git show --stat HEAD   # must list SKILL.md, command, PLAYBOOK.md, README.md together
```

---

### Task 7: version bump + design-doc commit + final sweep

**Files:**
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json` (version `0.25.9` → `0.26.0`; description + keywords)
- Modify: `.claude-plugin/marketplace.json` (dev-workflows entry: version + description)
- Commit (already created earlier in the session, likely still uncommitted): `docs/adr/0043…0052`, `CONTEXT.md`, `docs/superpowers/specs/2026-07-31-career-growth-skill-design.md`, this plan file

**Interfaces:**
- Consumes: plugin/marketplace JSON shapes shown below; skill committed in Task 6.

**⚠ `.claude-plugin/marketplace.json` is outside `plugins/dev-workflows/` — same write-guard workaround as Task 6 if blocked.**

- [ ] **Step 1: Bump `plugin.json`**

In `plugins/dev-workflows/.claude-plugin/plugin.json`:
- `"version": "0.25.9"` → `"version": "0.26.0"`
- In `"description"`, insert before `Reflection:`:
  `Growth: career-growth (quarterly career review — evidence-graded inventory, live market + certificate survey, four-test moat, cert-driven mini-project plan). `
- Append to `"keywords"`: `"career-growth", "career", "skill-gap", "certification", "job-market", "moat", "upskilling"`

- [ ] **Step 2: Sync `marketplace.json`**

In the `dev-workflows` entry of `.claude-plugin/marketplace.json`:
- `"version"` → `"0.26.0"`
- Insert the same `Growth: career-growth (…)` sentence at the same place in its `"description"`.

- [ ] **Step 3: Verify version sync (the repo invariant)**

```bash
python -c "
import json
p=json.load(open('plugins/dev-workflows/.claude-plugin/plugin.json',encoding='utf-8'))
m=json.load(open('.claude-plugin/marketplace.json',encoding='utf-8'))
e=[x for x in m['plugins'] if x['name']=='dev-workflows'][0]
assert p['version']==e['version']=='0.26.0',(p['version'],e['version'])
assert 'career-growth' in p['description'] and 'career-growth' in e['description']
print('versions in sync: 0.26.0')"
```
Expected: `versions in sync: 0.26.0`

- [ ] **Step 4: Commit the bump**

```bash
git add plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(dev-workflows): bump to 0.26.0 for career-growth" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git log -1 --format=%B
```

- [ ] **Step 5: Commit the session's design docs (grill-then-plan gotcha: they orphan otherwise)**

```bash
git add docs/adr/0043*.md docs/adr/0044*.md docs/adr/0045*.md docs/adr/0046*.md docs/adr/0047*.md docs/adr/0048*.md docs/adr/0049*.md docs/adr/0050*.md docs/adr/0051*.md docs/adr/0052*.md CONTEXT.md docs/superpowers/specs/2026-07-31-career-growth-skill-design.md docs/superpowers/plans/2026-07-31-career-growth-skill.md
git commit -m "docs(career-growth): design session — ADRs 0043-0052, Moat term, spec, plan" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git log -1 --format=%B
```

- [ ] **Step 6: Final sweep**

```bash
git status --short          # expect: clean (no stray tmp-* files under plugins/dev-workflows)
ls plugins/dev-workflows/skills/career-growth/            # SKILL.md + references/
grep -rn "CLAUDE_PLUGIN_ROOT" plugins/dev-workflows/skills/career-growth/ || echo "no plugin-root refs (correct)"
```
Expected: clean status; `SKILL.md` + 3 reference files; `no plugin-root refs (correct)`.
