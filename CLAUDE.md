# CLAUDE.md — workflow-daily-work

Orientation for an AI agent or new contributor working *in* this repo. For end-user
install/use, see [README.md](README.md). For deeper internals, see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). For term definitions, see
[CONTEXT.md](CONTEXT.md).

## What this is

A Claude Code **plugin marketplace** (`workflow-daily-work`). It ships three
**plugins**: `ado-backlog` (findings → Azure DevOps backlog, plus the assigned-work
view), `github-backlog` (the same pipeline against GitHub Issues), and
`dev-workflows` (the daily-work arc: the `/daily` router plus design, debugging,
review, study, and communication skills). [PLAYBOOK.md](PLAYBOOK.md) maps the whole
arc — when to reach for what.

## Repo layout

```
.claude-plugin/marketplace.json   the marketplace (lists the plugins)
CONTEXT.md                        glossary — domain + architecture terms
PLAYBOOK.md                       the daily-arc map — when to reach for what
README.md                         end-user overview + install
docs/
  ARCHITECTURE.md                 how it's built + how to extend
  superpowers/specs/              design specs
  superpowers/plans/              implementation plans
plugins/ado-backlog/
  .claude-plugin/plugin.json      the plugin manifest
  skills/<name>/SKILL.md          one capability per pipeline step
  commands/<name>.md              thin /ado-backlog:<name> entry points
  scripts/                        executables the skills call (.cs/.py/.ps1)
  references/data-contracts.md    canonical JSON schemas (single source of truth)
  docs/adr/                       accepted design decisions (ADRs)
  examples/                       sample fixtures for testing
  README.md, QUICKSTART.md        user docs
plugins/github-backlog/           same pipeline, GitHub Issues backend
plugins/dev-workflows/            daily-work arc skills + the /daily router
```

## Mental model

The plugin is a pipeline; each step is a skill; state flows through three JSON **data
contracts** joined by a stable `key`:

```
extract → triage (in-memory) → classify → create (dry-run gated) → write-back
  findings.json               → backlog_input.json → backlog_result.json
```

The orchestrator skill `findings-to-ado-backlog` sequences these steps and enforces the
safety gates; `ado-auth` is the optional pre-flight (Step 0) it delegates to before
extract. `my-work` (list assigned items) is a standalone query skill outside the
pipeline. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the step-by-step detail
and an add-a-skill recipe.

## Conventions (do not violate)

- **Skills** live in `plugins/ado-backlog/skills/<name>/SKILL.md` with YAML frontmatter
  (`name` + a trigger-rich `description`). Reference bundled files via
  `${CLAUDE_PLUGIN_ROOT}` — never hard-code paths.
- **Commands** are thin wrappers in `plugins/ado-backlog/commands/<name>.md`
  (`description` + `argument-hint` frontmatter) that hand off to a skill via
  `$ARGUMENTS`. Logic lives in the skill, not the command.
- **Data-contract schemas are defined only** in
  `plugins/ado-backlog/references/data-contracts.md`. Never redefine them elsewhere.
- **Keep versions in sync:** each plugin's `.claude-plugin/plugin.json` and its entry
  in `.claude-plugin/marketplace.json` must always report the same version.
- **Every new skill adds one row to [PLAYBOOK.md](PLAYBOOK.md)** — the playbook is the
  discoverability map for the daily arc; a skill missing from it is invisible. Add the
  row in the same commit that adds the skill.

## Key commands

Run these from a shell at the repo root (repo-relative paths). Inside a skill's
SKILL.md, reference scripts via `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` instead.

```powershell
# Verify prerequisites (az login, .NET >= 10, Python + openpyxl, org/project)
powershell -ExecutionPolicy Bypass -File "plugins/ado-backlog/scripts/setup_check.ps1"

# Dry run — validates against ADO, creates nothing (this is the DEFAULT)
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
