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

The plugin is decomposed into **one skill per pipeline step** (with `ado-auth` as the
optional pre-flight Step 0), plus the standalone `my-work` query skill, a few helper
**scripts**, and thin **commands**. The decomposition is deliberate: each step is
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
 source
   │  extract-findings
   ▼
 findings.json
   │  triage-findings          (filters in memory — produces no new file)
   ▼
 (scoped findings)
   │  classify-work-items
   ▼
 backlog_input.json
   │  ado-create-work-items    (dry-run validates → on approval, creates)
   ▼
 backlog_result.json
   │  ado-writeback-tracking   (spreadsheets only)
   ▼
 source  (ticket IDs/URLs written back beside each row)
```

The gate per step is in the table below; triage filters the findings in memory and does
**not** persist a fourth file.

| Step | Owning skill | Reads | Writes | Gate |
|------|--------------|-------|--------|------|
| Pre-flight: Auth | `ado-auth` | — | env: Entra token / `AZDO_*` | — |
| Extract | `extract-findings` | source file / pasted text | `findings.json` | confirm column mapping with user |
| Triage | `triage-findings` | `findings.json` | scoped findings (in memory) | — (recommends Critical+confirmed first) |
| Classify | `classify-work-items` | scoped findings | `backlog_input.json` | estimates gate (show hours, get OK) |
| Dry run | `ado-create-work-items` | `backlog_input.json` | validation PASS/FAIL list | dry-run creates nothing |
| Create | `ado-create-work-items` | `backlog_input.json` | `backlog_result.json` | **explicit user approval required** |
| Write-back | `ado-writeback-tracking` | `backlog_result.json` | updated source spreadsheet | back up the source first |

The **orchestrator** skill, `findings-to-ado-backlog`, sequences these six sibling
skills (auth → extract → triage → classify → create → write-back) and enforces the
gates. It is the teachable happy path; `/ado-backlog:run` wraps it. `my-work` is a
standalone query skill outside this pipeline.

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
`${CLAUDE_PLUGIN_ROOT}/scripts/<name>` (`${CLAUDE_PLUGIN_ROOT}` is injected by the
plugin runtime and resolves to the plugin's installed root). The `.cs` scripts run as
file-based apps via `dotnet run <file>.cs` — a .NET 10 feature, hence the .NET 10 SDK
prerequisite.

| Script | Purpose | Invocation |
|--------|---------|------------|
| `read_source.py` | Dump a spreadsheet (xlsx/csv/tsv) to UTF-8 text so it survives the cp1252 console | `python "${CLAUDE_PLUGIN_ROOT}/scripts/read_source.py" "<file>"` |
| `create-backlog.cs` | Create work items in ADO from `backlog_input.json`; dry-run by default; writes `backlog_result.json` | `dotnet run "${CLAUDE_PLUGIN_ROOT}/scripts/create-backlog.cs" -- "<workdir>/backlog_input.json"` |
| `my-work.cs` | Query the caller's assigned ADO work items and render them as a table | `dotnet run "${CLAUDE_PLUGIN_ROOT}/scripts/my-work.cs"` |
| `tracking.py` | Add tracking columns to the source spreadsheet and write created ticket IDs/URLs back, matched by `key` | `python "${CLAUDE_PLUGIN_ROOT}/scripts/tracking.py" ...` |
| `setup_check.ps1` | Verify prerequisites: `az login`, .NET >= 10, Python + openpyxl, `AZDO_ORG`/`AZDO_PROJECT` | `powershell -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check.ps1"` |

## Planned / in progress (NOT on disk yet)

> ⚠️ The following is **designed but not yet implemented**. These files do **not** exist
> in `plugins/ado-backlog/scripts/` — do not call them.

**Org/project auto-discovery** would remove the manual `AZDO_ORG` / `AZDO_PROJECT`
setup by discovering them from the Azure CLI, with a layered fallback and a self-priming
config cache. Planned files: `resolve-ado-target.ps1` (dot-sourceable entry),
`AdoTarget.psm1` (helper module), `AdoTarget.Tests.ps1` (Pester tests).

See the [az-ado-target-discovery plan](superpowers/plans/2026-06-02-az-ado-target-discovery.md)
and [ADR 0002 — az org/project discovery](../plugins/ado-backlog/docs/adr/0002-az-org-project-discovery.md).

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

8. **If the skill generates Markdown documents**, point it at the diagram convention —
   `plugins/dev-workflows/references/diagram-convention.md` (one overview Mermaid
   diagram at the top, type-matched diagrams per section, ask-gate for destinations
   that don't render Mermaid). See marketplace ADRs 0005–0009.

9. **Bump versions in sync.** Update `version` in
   `plugins/ado-backlog/.claude-plugin/plugin.json` and the matching plugin entry in
   `.claude-plugin/marketplace.json` together — they must always report the same version.
   (The *top-level* `version` in `marketplace.json` is the marketplace's own version,
   separate from any plugin's; bump it when you add or remove a plugin.)
