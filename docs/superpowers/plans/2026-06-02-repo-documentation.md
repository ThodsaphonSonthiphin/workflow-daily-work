# Repo Documentation (CLAUDE.md + ARCHITECTURE.md) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a root `CLAUDE.md` and a `docs/ARCHITECTURE.md` so an AI agent or new contributor can understand and safely extend this Claude Code plugin marketplace without reading source first.

**Architecture:** Two new Markdown files. `CLAUDE.md` is the always-in-context orientation file (concise, links out). `docs/ARCHITECTURE.md` is the read-on-demand deep dive (pipeline model, design principles, scripts-that-exist-today, a fenced "Planned" section, and a worked add-a-skill recipe). Both link to existing docs rather than duplicating them. No existing docs are edited. `CONTEXT.md` glossary was already updated this session.

**Tech Stack:** Markdown only. Verification via PowerShell `Test-Path` and ripgrep checks on Windows.

**Source spec:** [docs/superpowers/specs/2026-06-02-repo-documentation-design.md](../specs/2026-06-02-repo-documentation-design.md)

**Ground-truth facts (verified on disk 2026-06-02):**
- Scripts that EXIST: `create-backlog.cs`, `my-work.cs`, `read_source.py`, `setup_check.ps1`, `tracking.py` (all in `plugins/ado-backlog/scripts/`).
- Scripts that are PLANNED / ABSENT: `resolve-ado-target.ps1`, `AdoTarget.psm1`, `AdoTarget.Tests.ps1`.
- `plugins/ado-backlog/examples/` contains `sample-backlog_input.json` and `sample-findings.csv`.
- 8 skills under `plugins/ado-backlog/skills/`: ado-auth, ado-create-work-items, ado-writeback-tracking, classify-work-items, extract-findings, findings-to-ado-backlog (orchestrator), my-work, triage-findings.
- 3 commands under `plugins/ado-backlog/commands/`: my-work.md, run.md, setup-check.md.
- 2 ADRs under `docs/adr/`: 0001-estimate-as-child-task-hours.md, 0002-az-org-project-discovery.md.
- Both `marketplace.json` and `plugin.json` are version `0.2.0`.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `CLAUDE.md` (root) — **Create** | Always-in-context agent/contributor orientation: what the repo is, layout, mental model, conventions, key commands, environment gotchas, safety gates, pointers. Concise. |
| `docs/ARCHITECTURE.md` — **Create** | Read-on-demand internals: pipeline step-by-step + diagram, design principles, exists-today scripts table, fenced Planned section, add-a-skill recipe. |
| `CONTEXT.md` — **Done already** (not a task) | Glossary; "Repo architecture terms" block added this session. |

---

## Task 1: Create `docs/ARCHITECTURE.md`

ARCHITECTURE.md is created first because CLAUDE.md links to it; creating it first means CLAUDE.md's link is valid the moment it is written.

**Files:**
- Create: `docs/ARCHITECTURE.md`

- [ ] **Step 1: Verify the ground-truth facts before writing**

Confirm the exists/absent script lists are still true, so no claim is stale.

Run (PowerShell, from repo root `c:\Repo2\workflow daily work`):
```powershell
"create-backlog.cs","my-work.cs","read_source.py","setup_check.ps1","tracking.py" | ForEach-Object {
  "{0,-22} {1}" -f $_, (Test-Path "plugins/ado-backlog/scripts/$_")
}
"resolve-ado-target.ps1","AdoTarget.psm1","AdoTarget.Tests.ps1" | ForEach-Object {
  "{0,-22} {1}" -f $_, (Test-Path "plugins/ado-backlog/scripts/$_")
}
```
Expected: first five print `True`; last three print `False`. If any differ, STOP and reconcile the doc against reality before writing.

- [ ] **Step 2: Write `docs/ARCHITECTURE.md` with exactly this content**

```markdown
# Architecture — workflow-daily-work

How this repo is built and how to extend it. For *using* the plugin, see the
[plugin README](../plugins/ado-backlog/README.md) and
[QUICKSTART](../plugins/ado-backlog/QUICKSTART.md). For term definitions, see
[CONTEXT.md](../CONTEXT.md).

## Overview

This repo is a **Claude Code plugin marketplace** (`workflow-daily-work`) declared in
[.claude-plugin/marketplace.json](../.claude-plugin/marketplace.json). It currently
ships one **plugin**, `ado-backlog`, defined by
[plugins/ado-backlog/.claude-plugin/plugin.json](../plugins/ado-backlog/.claude-plugin/plugin.json).

The plugin is decomposed into **one skill per pipeline step**, plus a small number of
helper **scripts** and thin **commands**. The decomposition is deliberate: each step is
reusable on its own, and the steps communicate only through small JSON files, so any
step can be run, tested, or replaced in isolation.

```
plugins/ado-backlog/
├── skills/        one SKILL.md per step (the capabilities)
├── commands/      thin /ado-backlog:<name> entry points
├── scripts/       executables the skills call (.cs / .py / .ps1)
├── references/    data-contracts.md — the canonical JSON schemas
└── examples/      sample fixtures for testing
```

## The pipeline, step by step

State flows through **three JSON data contracts**, each joined to the next by a stable
`key` per finding (a row number or ID column) so a created ticket can be traced back to
its source row. The canonical shapes live in
[references/data-contracts.md](../plugins/ado-backlog/references/data-contracts.md) —
that file is the single source of truth; this document does not restate the schemas.

```
                 findings.json          backlog_input.json        backlog_result.json
                 ┌──────────┐           ┌──────────────┐          ┌────────────────┐
 source  ──▶ extract ──▶    │ ──▶ triage ──▶ classify ──▶         │ ──▶ create ──▶  │ ──▶ write-back ──▶ source
                 └──────────┘  (filter)  └──────────────┘  (gate)  └────────────────┘   (spreadsheets only)
                                                              dry-run + approval
```

| Step | Owning skill | Reads | Writes | Gate |
|------|--------------|-------|--------|------|
| Extract | `extract-findings` | source file / pasted text | `findings.json` | confirm column mapping with user |
| Triage | `triage-findings` | `findings.json` | scoped subset of findings | — (recommends Critical+confirmed first) |
| Classify | `classify-work-items` | scoped findings | `backlog_input.json` | estimates gate (show hours, get OK) |
| Dry run | `ado-create-work-items` | `backlog_input.json` | validation PASS/FAIL list | dry-run creates nothing |
| Create | `ado-create-work-items` | `backlog_input.json` | `backlog_result.json` | **explicit user approval required** |
| Write-back | `ado-writeback-tracking` | `backlog_result.json` | updated source spreadsheet | back up the source first |

The **orchestrator** skill, `findings-to-ado-backlog`, sequences all six steps and
enforces the gates. It is the teachable happy path; `/ado-backlog:run` wraps it.

## Design principles

- **Data-contract-first.** Steps communicate *only* through the three JSON files, so
  each skill is reusable standalone and testable without the others. Schemas are defined
  in one place (`references/data-contracts.md`) and nowhere else.
- **The orchestrator owns sequencing and gates, not logic.** Each step's logic lives in
  its own skill; `findings-to-ado-backlog` only orders them and stops at the gates.
- **Gates exist because creating work items is an irreversible external write.** The
  pipeline stages read-only work first, then a dry run that creates nothing, then an
  explicit human approval, then the real write — so nothing the user can't easily undo
  happens without them seeing it first.

## Scripts (exist today)

All scripts live in `plugins/ado-backlog/scripts/`. Skills reference them via
`${CLAUDE_PLUGIN_ROOT}/scripts/<name>`.

| Script | Purpose | Invocation |
|--------|---------|------------|
| `read_source.py` | Dump a spreadsheet (xlsx/csv/tsv) to UTF-8 text so it survives the cp1252 console | `python "${CLAUDE_PLUGIN_ROOT}/scripts/read_source.py" "<file>"` |
| `create-backlog.cs` | Create work items in ADO from `backlog_input.json`; dry-run by default; writes `backlog_result.json` | `dotnet run "${CLAUDE_PLUGIN_ROOT}/scripts/create-backlog.cs" -- "<workdir>/backlog_input.json"` |
| `my-work.cs` | Query the caller's assigned ADO work items and render them as a table | `dotnet run "${CLAUDE_PLUGIN_ROOT}/scripts/my-work.cs"` |
| `tracking.py` | Add tracking columns to the source spreadsheet and write created ticket IDs/URLs back, matched by `key` | `python "${CLAUDE_PLUGIN_ROOT}/scripts/tracking.py" ...` |
| `setup_check.ps1` | Verify prerequisites: `az login`, .NET ≥ 10, Python + openpyxl, `AZDO_ORG`/`AZDO_PROJECT` | `powershell -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check.ps1"` |

## Planned / in progress (NOT on disk yet)

> ⚠️ The following is **designed but not yet implemented**. These files do **not** exist
> in `plugins/ado-backlog/scripts/` — do not call them.

**Org/project auto-discovery** would remove the manual `AZDO_ORG` / `AZDO_PROJECT`
setup by discovering them from the Azure CLI, with a layered fallback and a self-priming
config cache. Planned files: `resolve-ado-target.ps1` (dot-sourceable entry),
`AdoTarget.psm1` (helper module), `AdoTarget.Tests.ps1` (Pester tests).

See the plan
[docs/superpowers/plans/2026-06-02-az-ado-target-discovery.md](plans/2026-06-02-az-ado-target-discovery.md)
and [docs/adr/0002-az-org-project-discovery.md](adr/0002-az-org-project-discovery.md).

## Adding a new skill (worked recipe)

Follow these steps to add a step to the pipeline using the repo's conventions. You
should not need to read existing source first.

1. **Create the skill file** at `plugins/ado-backlog/skills/<name>/SKILL.md` with YAML
   frontmatter — `name` plus a trigger-rich `description` (a folded `>-` scalar listing
   the phrases a user would actually say, so the model knows when to invoke it). Pattern:

   ```yaml
   ---
   name: <name>
   description: >-
     One-line what-it-does, then the trigger phrases ("turn this into...",
     "file these as...", etc.). Name the skill it hands off to next.
   ---
   ```

2. **Define or reuse its data contract.** If the skill introduces or transforms one of
   the JSON files, document the shape in
   `plugins/ado-backlog/references/data-contracts.md` (the only place schemas live).
   Reuse the existing stable `key` so findings stay traceable end-to-end.

3. **Reference bundled files via `${CLAUDE_PLUGIN_ROOT}`** — never hard-code paths. E.g.
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/<helper>.py"`.

4. **Wire it into the orchestrator.** Add the step to
   `plugins/ado-backlog/skills/findings-to-ado-backlog/SKILL.md` at the correct point in
   the sequence, and state which gate (if any) precedes it. If it performs an
   irreversible write, it must sit behind a dry-run + explicit-approval gate.

5. **(Optional) Add a command** at `plugins/ado-backlog/commands/<name>.md` — a thin
   wrapper (`description` + `argument-hint` frontmatter) that hands off to the skill via
   `$ARGUMENTS`. Only add one if the step deserves its own `/ado-backlog:<name>` entry.

6. **Put any helper script in `plugins/ado-backlog/scripts/`** and document its
   invocation in the skill (`.cs` → `dotnet run`, `.py` → `python`, `.ps1` →
   `powershell -ExecutionPolicy Bypass -File`).

7. **Test it.** Run `/ado-backlog:setup-check`, then exercise the skill end-to-end using
   the fixtures in `plugins/ado-backlog/examples/` (`sample-findings.csv`,
   `sample-backlog_input.json`). For anything that writes to ADO, validate via the
   dry-run path before a real run.

8. **Bump versions in sync.** Update `version` in
   `plugins/ado-backlog/.claude-plugin/plugin.json`, and the matching plugin entry in
   `.claude-plugin/marketplace.json`. They are both `0.2.0` today and must not drift.
```

- [ ] **Step 3: Verify the file was created and is non-trivial**

Run:
```powershell
Test-Path "docs/ARCHITECTURE.md"; (Get-Content "docs/ARCHITECTURE.md" | Measure-Object -Line).Lines
```
Expected: `True`, and a line count well over 80.

- [ ] **Step 4: Verify no PLANNED-only script is described as callable**

The planned scripts may only appear inside the fenced "Planned" section, never in an
invocation. Check that the exists-today table and recipe never invoke a planned file:
```powershell
Select-String -Path "docs/ARCHITECTURE.md" -Pattern "resolve-ado-target|AdoTarget" |
  Select-Object LineNumber, Line
```
Expected: matches appear ONLY in the "Planned / in progress" section (and its links) — none inside a `dotnet run` / `python` / `powershell` invocation or the scripts-that-exist table. If any appears elsewhere, fix it.

- [ ] **Step 5: Verify every exists-today script referenced actually exists**

```powershell
"read_source.py","create-backlog.cs","my-work.cs","tracking.py","setup_check.ps1" | ForEach-Object {
  if (-not (Test-Path "plugins/ado-backlog/scripts/$_")) { "MISSING: $_" }
}
```
Expected: no output (all present).

- [ ] **Step 6: Commit**

```powershell
git add "docs/ARCHITECTURE.md"
git commit -m @'
docs: add ARCHITECTURE.md (pipeline, principles, add-a-skill recipe)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
'@
```

---

## Task 2: Create root `CLAUDE.md`

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Write `CLAUDE.md` with exactly this content**

```markdown
# CLAUDE.md — workflow-daily-work

Orientation for an AI agent or new contributor working *in* this repo. For end-user
install/use, see [README.md](README.md). For deeper internals, see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). For term definitions, see
[CONTEXT.md](CONTEXT.md).

## What this is

A Claude Code **plugin marketplace** (`workflow-daily-work`). It currently ships one
**plugin**, `ado-backlog`, which turns findings (an audit spreadsheet, a doc, a review,
a pasted list of issues) into an Azure DevOps backlog of linked work items, and surfaces
a person's assigned work.

## Repo layout

```
.claude-plugin/marketplace.json   the marketplace (lists the plugins)
CONTEXT.md                        glossary — domain + architecture terms
README.md                         end-user overview + install
docs/
  ARCHITECTURE.md                 how it's built + how to extend
  adr/                            accepted design decisions (ADRs)
  superpowers/{specs,plans}/      design specs + implementation plans
plugins/ado-backlog/
  .claude-plugin/plugin.json      the plugin manifest
  skills/<name>/SKILL.md          one capability per pipeline step
  commands/<name>.md              thin /ado-backlog:<name> entry points
  scripts/                        executables the skills call (.cs/.py/.ps1)
  references/data-contracts.md    canonical JSON schemas (single source of truth)
  examples/                       sample fixtures for testing
  README.md, QUICKSTART.md        user docs
```

## Mental model

The plugin is a pipeline; each step is a skill; state flows through three JSON **data
contracts** joined by a stable `key`:

```
extract → triage → classify → dry-run → create → write-back
  findings.json → backlog_input.json → backlog_result.json
```

The orchestrator skill `findings-to-ado-backlog` sequences the steps and enforces the
safety gates. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the step-by-step
detail and an add-a-skill recipe.

## Conventions (do not violate)

- **Skills** live in `plugins/ado-backlog/skills/<name>/SKILL.md` with YAML frontmatter
  (`name` + a trigger-rich `description`). Reference bundled files via
  `${CLAUDE_PLUGIN_ROOT}` — never hard-code paths.
- **Commands** are thin wrappers in `plugins/ado-backlog/commands/<name>.md`
  (`description` + `argument-hint` frontmatter) that hand off to a skill via
  `$ARGUMENTS`. Logic lives in the skill, not the command.
- **Data-contract schemas are defined only** in
  `plugins/ado-backlog/references/data-contracts.md`. Never redefine them elsewhere.
- **Keep versions in sync:** `plugins/ado-backlog/.claude-plugin/plugin.json` and the
  plugin entry in `.claude-plugin/marketplace.json` (both `0.2.0` today).

## Key commands

```powershell
# Verify prerequisites (az login, .NET >= 10, Python + openpyxl, org/project)
powershell -ExecutionPolicy Bypass -File "plugins/ado-backlog/scripts/setup_check.ps1"

# Dry run — validates against ADO, creates nothing
$env:AZDO_DRY_RUN = "true"
dotnet run "plugins/ado-backlog/scripts/create-backlog.cs" -- "<workdir>/backlog_input.json"

# Real run — only after explicit user approval of the dry-run result
$env:AZDO_DRY_RUN = "false"
dotnet run "plugins/ado-backlog/scripts/create-backlog.cs" -- "<workdir>/backlog_input.json"
```

Run scripts by type: `.cs` → `dotnet run`, `.py` → `python`, `.ps1` →
`powershell -ExecutionPolicy Bypass -File`.

## Environment & gotchas

- **Windows + PowerShell.** Use PowerShell syntax (`$env:VAR`, not `$VAR`).
- **cp1252 console trap:** don't open spreadsheets blind — dump them to UTF-8 first with
  `read_source.py`, then read the dump.
- **ADO auth** defaults to an Entra token
  (`az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798`); an
  `AZDO_PAT` env var is the fallback. See the `ado-auth` skill.
- **`AZDO_ORG` / `AZDO_PROJECT` are bare names** (e.g. `Cartagena365`, `GlassHull`), not
  URLs and not the Azure subscription/tenant. See [CONTEXT.md](CONTEXT.md).

## Safety gates (non-negotiable)

1. **Never create in ADO before a passing dry-run.**
2. **Never create without explicit user approval** of the validated list.
3. **Back up the source spreadsheet before write-back** (it edits the file in place).

The `findings-to-ado-backlog` orchestrator owns the canonical wording of these gates.

## Pointers

- [CONTEXT.md](CONTEXT.md) — glossary (Organization, Project, Skill, Orchestrator, …)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — internals + add-a-skill recipe
- [docs/adr/](docs/adr/) — accepted design decisions
- [plugins/ado-backlog/README.md](plugins/ado-backlog/README.md) /
  [QUICKSTART.md](plugins/ado-backlog/QUICKSTART.md) — user docs
```

- [ ] **Step 2: Verify the file was created**

Run:
```powershell
Test-Path "CLAUDE.md"; (Get-Content "CLAUDE.md" | Measure-Object -Line).Lines
```
Expected: `True`, and a line count between roughly 70 and 130 (concise — if it is much larger, trim, since this file loads into context every session).

- [ ] **Step 3: Verify every internal link target exists**

Every relative path CLAUDE.md links to must resolve on disk.
```powershell
"README.md","CONTEXT.md","docs/ARCHITECTURE.md","docs/adr",
"plugins/ado-backlog/README.md","plugins/ado-backlog/QUICKSTART.md",
"plugins/ado-backlog/references/data-contracts.md",
"plugins/ado-backlog/scripts/setup_check.ps1",
"plugins/ado-backlog/scripts/create-backlog.cs" | ForEach-Object {
  if (-not (Test-Path $_)) { "BROKEN LINK TARGET: $_" }
}
```
Expected: no output (all link targets exist).

- [ ] **Step 4: Verify no planned-only script is referenced**

```powershell
Select-String -Path "CLAUDE.md" -Pattern "resolve-ado-target|AdoTarget"
```
Expected: no output (CLAUDE.md must not mention the unbuilt scripts at all).

- [ ] **Step 5: Commit**

```powershell
git add "CLAUDE.md"
git commit -m @'
docs: add root CLAUDE.md for agent + contributor orientation

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
'@
```

---

## Task 3: Final cross-check against the spec's acceptance criteria

**Files:** none (verification only).

- [ ] **Step 1: Confirm both files exist and link to each other**

```powershell
Test-Path "CLAUDE.md"; Test-Path "docs/ARCHITECTURE.md"
Select-String -Path "CLAUDE.md" -Pattern "docs/ARCHITECTURE.md" | Measure-Object | % Count
Select-String -Path "docs/ARCHITECTURE.md" -Pattern "data-contracts.md" | Measure-Object | % Count
```
Expected: both `True`; both counts ≥ 1 (CLAUDE.md links to ARCHITECTURE.md; ARCHITECTURE.md links to the data-contracts source of truth).

- [ ] **Step 2: Confirm no doc redefines a JSON schema (link, don't duplicate)**

ARCHITECTURE.md and CLAUDE.md should *point to* `data-contracts.md`, not restate field
tables. Spot-check that neither file contains a full schema block:
```powershell
Select-String -Path "CLAUDE.md","docs/ARCHITECTURE.md" -Pattern '"System\.Title"|"Microsoft\.VSTS' | Select-Object Path, LineNumber
```
Expected: no output (raw ADO field reference names live only in `data-contracts.md` and the skills).

- [ ] **Step 3: Confirm existing user docs were not modified**

```powershell
git status --porcelain
```
Expected: only `CLAUDE.md`, `docs/ARCHITECTURE.md` (and, if not yet committed, `CONTEXT.md`) appear — no changes to `README.md`, `QUICKSTART.md`, or any `SKILL.md`. (The two new files should already be committed from Tasks 1–2, so a clean tree is also acceptable.)

- [ ] **Step 4: Report acceptance-criteria results to the user**

Summarize, against the spec's acceptance criteria: both files created; every internal
claim verified true on disk; no planned-only file described as callable; docs link to
(not duplicate) data-contracts.md / CONTEXT.md / READMEs; existing docs untouched.
```
