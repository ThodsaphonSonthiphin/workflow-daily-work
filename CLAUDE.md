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
  superpowers/{specs,plans}/      design specs + implementation plans
plugins/ado-backlog/
  .claude-plugin/plugin.json      the plugin manifest
  skills/<name>/SKILL.md          one capability per pipeline step
  commands/<name>.md              thin /ado-backlog:<name> entry points
  scripts/                        executables the skills call (.cs/.py/.ps1)
  references/data-contracts.md    canonical JSON schemas (single source of truth)
  docs/adr/                       accepted design decisions (ADRs)
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
safety gates. `ado-auth` (authentication) and `my-work` (list assigned items) are
standalone skills outside the pipeline. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
for the step-by-step detail and an add-a-skill recipe.

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
  plugin entry in `.claude-plugin/marketplace.json` must always report the same version.

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

Run scripts by type: `.cs` → `dotnet run` (file-based app, .NET 10), `.py` → `python`,
`.ps1` → `powershell -ExecutionPolicy Bypass -File`.

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
- [plugins/ado-backlog/docs/adr/](plugins/ado-backlog/docs/adr/) — accepted design decisions (ADRs)
- [plugins/ado-backlog/README.md](plugins/ado-backlog/README.md) /
  [QUICKSTART.md](plugins/ado-backlog/QUICKSTART.md) — user docs
