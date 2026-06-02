# ado-backlog

Turn findings from **any input** into an **Azure DevOps backlog** — safely and traceably.
Built for repeatable team use: each step is a small reusable skill, and a thin orchestrator
chains them with safety gates.

## The flow

```
extract-findings → triage-findings → classify-work-items → ado-create-work-items → ado-writeback-tracking
   (any input)        (scope it)       (types per process)   (DRY-RUN then create)     (links back to source)
```

`findings-to-ado-backlog` runs the whole thing; `/ado-backlog:run <file>` is the shortcut.

## Skills (each is also a slash command: `/ado-backlog:<name>`)

| Skill | What it does |
|---|---|
| `extract-findings` | Read any source (xlsx/csv via a helper; docs/text directly) → normalized `findings.json`. |
| `triage-findings` | Filter/scope by severity, status, kind; pick the wave to file first. |
| `classify-work-items` | Discover the project's **process** (Agile/Scrum/Basic/CMMI), map findings to valid types + a parent, and propose a **time estimate** per item (a child Task carrying hours) → `backlog_input.json`. |
| `ado-auth` | Get an ADO token the standard way; troubleshoot 401/403/org errors. |
| `ado-create-work-items` | Create from `backlog_input.json`: **dry-run first**, real only on approval → `backlog_result.json`. |
| `ado-writeback-tracking` | Add tracking columns and write ticket IDs/URLs back to a spreadsheet source. |
| `findings-to-ado-backlog` | **Orchestrator** — the end-to-end pipeline with gates. |
| `my-work` | List *your* assigned ADO work items as a grouped table with clickable ticket links — open work first, by priority (daily "what's on my plate"). |

## Commands

- **`/ado-backlog:run <file-or-text>`** — run the full pipeline (wraps the orchestrator).
- **`/ado-backlog:my-work`** — show your assigned work items as a table with clickable ticket links.
- **`/ado-backlog:setup-check`** — verify prerequisites (az login, .NET 10, Python+openpyxl, org/project).

## Prerequisites & auth

- **Azure CLI** + `az login` (the scripts fetch a short-lived Microsoft Entra token for ADO),
  or set `$env:AZDO_PAT` (PAT with *Work Items: Read & Write*).
- **.NET 10 SDK** (the creator is a file-based `.cs` program), **Python 3** + `openpyxl`.
- Point at your board: `$env:AZDO_ORG` and `$env:AZDO_PROJECT` (or the skill asks).

## Assignment

A fresh backlog is created **unassigned** by default; the orchestrator **asks who to assign
to**. Assign per item (`System.AssignedTo` in `backlog_input.json`) or the whole batch at once
with `$env:AZDO_ASSIGNED_TO = "name@your-domain"`. A bad identity fails the dry-run, never the board.

## Safety gates (why this is trustworthy to hand a colleague)

1. **Dry-run before real** — every create is validated with `validateOnly=true` first; creates nothing.
2. **Explicit approval** — the real write happens only after the user says yes.
3. **Back up before write-back** — write-back edits the source spreadsheet in place.
4. **Idempotent write-back** — rows already carrying a Ticket ID are left alone, so re-runs are safe.

## How the steps connect

Three small JSON files carry state, linked by a stable **`key`** per finding. Full shapes:
[`references/data-contracts.md`](references/data-contracts.md). Worked example in
[`examples/`](examples/).

## Generalization

Nothing is hardcoded to one org/project. Each colleague runs their own `az login` and points
`AZDO_ORG`/`AZDO_PROJECT` at their board. The classify step adapts to whatever process that
project uses.
