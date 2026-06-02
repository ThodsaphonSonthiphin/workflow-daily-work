# Design Spec — Repo Documentation for AI Agents & Contributors

**Date:** 2026-06-02
**Topic:** repo-documentation
**Status:** Draft — awaiting approval before handoff to `superpowers:writing-plans`

## Problem

The repo documents how to *use* the `ado-backlog` plugin (root `README.md`, plugin
`README.md`, `QUICKSTART.md`) and pins domain terms (`CONTEXT.md`), but there is
**no entry point that orients an AI agent or a new contributor on how the repo works
internally and how to extend it safely.** There is no `CLAUDE.md` anywhere, and no
architecture/contributor document. An agent dropped into the repo today has to
reverse-engineer the pipeline, the skill-chaining pattern, and the conventions from
source.

## Goal

After this change, an AI agent or a new contributor can, within minutes:

1. Understand what the repo is (a Claude Code plugin marketplace shipping one plugin),
   how it is laid out, and where each kind of thing lives.
2. Understand the `ado-backlog` pipeline as a mental model — the steps, how skills
   chain via JSON data contracts, and the safety gates.
3. Follow a concrete, executable recipe to **add a new skill** to the pipeline using
   the repo's existing conventions.
4. Know the environment gotchas and key commands needed to work in the repo.

Non-goal: rewriting the existing user-facing docs (README, QUICKSTART, SKILL.md
files). They stay as-is; the new docs link to them rather than duplicate them.

## Decisions (from the grilling session)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Primary objective | Onboard **AI agents + contributors** (internal orientation), leave user-facing READMEs unchanged. |
| 2 | File structure | A concise **root `CLAUDE.md`** + a deeper **`docs/ARCHITECTURE.md`**. Scales as more plugins are added. |
| 3 | In-flight work | **Document reality, flag planned.** Only on-disk code is described as working; the org/project auto-discovery is a clearly-labeled "Planned" pointer to its plan + ADR 0002. |
| 4 | "How to extend" depth | A **concrete worked recipe** for adding a skill (the data-contract-first pattern, spelled out step-by-step). |

Supporting glossary terms (Marketplace, Plugin, Skill, Command, Orchestrator, Data
contract, Safety gate) were added to `CONTEXT.md` during the session.

## Artifacts

### 1. `CLAUDE.md` (repo root) — NEW

Short (always loaded into agent context every session — must not bloat). Links out
rather than duplicates. Sections:

- **What this is** — one paragraph: a Claude Code plugin *marketplace*
  (`workflow-daily-work`) currently shipping one plugin, `ado-backlog`. Point to
  `README.md` for end-user install/use.
- **Repo layout** — annotated tree (marketplace.json, `plugins/ado-backlog/{skills,
  commands,scripts,references,examples}`, `docs/`). One line per entry on *what lives
  there*, not what each file does.
- **Mental model (1 paragraph + 3-line diagram)** — the
  `extract → triage → classify → dry-run → create → write-back` pipeline; each step is
  a skill; state flows through three JSON data contracts keyed by a stable `key`; the
  orchestrator (`findings-to-ado-backlog`) sequences them and enforces the gates.
  Link to `docs/ARCHITECTURE.md` for detail.
- **Conventions** — the load-bearing rules an agent must not violate:
  - Skills live in `skills/<name>/SKILL.md` with YAML frontmatter (`name` +
    trigger-rich `description`); reference bundled files via `${CLAUDE_PLUGIN_ROOT}`.
  - Commands are thin wrappers in `commands/<name>.md` (`description` +
    `argument-hint`) that delegate to a skill via `$ARGUMENTS`.
  - Data-contract shapes are defined **only** in `references/data-contracts.md`; never
    redefine schemas elsewhere.
  - Keep `plugin.json` and `marketplace.json` versions in sync (both `0.2.0` today).
- **Key commands** — `setup-check`, the dry-run/real-run create invocations, how to
  run each script type (`dotnet run` for `.cs`, `python` for `.py`,
  `powershell -ExecutionPolicy Bypass -File` for `.ps1`).
- **Environment & gotchas** — Windows + PowerShell; the cp1252 console trap (dump
  spreadsheets to UTF-8 via `read_source.py`, don't open blind); ADO auth defaults to
  an Entra token (`az account get-access-token`), `AZDO_PAT` as fallback; `AZDO_ORG` /
  `AZDO_PROJECT` are bare names, not URLs (point to `CONTEXT.md`).
- **Safety gates (non-negotiable)** — never create in ADO before a passing dry-run and
  explicit user approval; back up the source before write-back. (Link to the
  orchestrator skill, which owns the canonical wording.)
- **Pointers** — `CONTEXT.md` (glossary), `docs/ARCHITECTURE.md` (internals),
  `docs/adr/` (decisions), plugin `README.md` / `QUICKSTART.md` (user docs).

### 2. `docs/ARCHITECTURE.md` — NEW

Read-on-demand depth. Sections:

- **Overview** — the marketplace → plugin → (skills | commands | scripts |
  references) structure, and why the plugin is decomposed into one-skill-per-step.
- **The pipeline, step by step** — for each of the six steps: which skill owns it,
  what it reads, what it writes, and the gate (if any) attached. A single diagram
  showing the three JSON files flowing between steps, keyed by `key`. Link the
  canonical schemas in `references/data-contracts.md` (do not restate them).
- **Design principles** — data-contract-first (steps communicate only through the JSON
  files, so each is reusable standalone); the orchestrator owns sequencing + gates, not
  logic; gates exist because creation is an irreversible external write.
- **Scripts** — table of the scripts that **exist today** (`create-backlog.cs`,
  `my-work.cs`, `read_source.py`, `setup_check.ps1`, `tracking.py`) with one-line
  purpose + how each is invoked.
- **Planned / in progress** — clearly fenced. Org/project auto-discovery
  (`resolve-ado-target.ps1`, `AdoTarget.psm1`, `AdoTarget.Tests.ps1`) is **designed,
  not yet built**; link `docs/superpowers/plans/2026-06-02-az-ado-target-discovery.md`
  and `docs/adr/0002-az-org-project-discovery.md`. State plainly these files are not on
  disk yet, so an agent does not try to call them.
- **Adding a new skill (worked recipe)** — concrete, executable checklist:
  1. Create `skills/<name>/SKILL.md`; frontmatter `name` + trigger-rich `description`
     (show the folded-scalar pattern and that triggers should include the phrases a
     user would actually say).
  2. Define its input/output in `references/data-contracts.md` if it introduces or
     transforms a contract; reuse the existing `key` join.
  3. Reference bundled scripts/refs via `${CLAUDE_PLUGIN_ROOT}`.
  4. Wire it into the `findings-to-ado-backlog` orchestrator at the right step, and
     state which gate (if any) precedes it.
  5. (Optional) add a `commands/<name>.md` thin wrapper if it deserves a `/` entry
     point.
  6. Put any helper script in `scripts/`; document its invocation.
  7. Test: run `setup-check`, then exercise the skill end-to-end (use `examples/` as a
     fixture); for ADO writes, validate via the dry-run path first.
  8. Bump `plugin.json` (and `marketplace.json` if the plugin entry changes); keep
     versions in sync.

### 3. `CONTEXT.md` — UPDATED (done during session)

Added a "Repo architecture terms" section pinning Marketplace, Plugin, Skill, Command,
Orchestrator, Data contract, Safety gate so the new docs use them precisely.

## Out of scope

- Editing the existing user-facing docs (README, QUICKSTART, the 8 SKILL.md files).
- Implementing the planned az-discovery scripts (documented as "planned", not built).
- New ADRs — the doc-structure choices here are reversible and unsurprising.

## Acceptance criteria

- `CLAUDE.md` exists at the repo root, is concise, and every internal claim it makes is
  true of the code on disk today.
- `docs/ARCHITECTURE.md` exists with the pipeline model, design principles, the
  exists-today scripts table, a clearly-fenced "Planned" section, and the step-by-step
  add-a-skill recipe.
- No doc describes a script or file that is not on disk as if it were callable.
- ARCHITECTURE.md and CLAUDE.md link to (not duplicate) `references/data-contracts.md`,
  `CONTEXT.md`, and the existing READMEs.
- A reader who follows the recipe can add a skill without reading source first.
