# Workflow Daily Work — Claude Code marketplace

A Claude Code **plugin marketplace** for daily-work automation. It ships three plugins:

- **`ado-backlog`** — turn findings from *any* input (an Excel/CSV audit, a doc, a code/QA
  review, a pasted list of issues) into an **Azure DevOps backlog**: extract → triage →
  classify by your project's process → **dry-run** → create on approval → write ticket links
  back to the source. Each step is its own reusable skill, plus a one-shot orchestrator.
- **`github-backlog`** — the same findings pipeline against **GitHub Issues**: labels +
  milestone classification, a visual dry-run gate, a tracking issue, and write-back.
- **`dev-workflows`** — the **daily-work arc**: the `/daily` router plus design
  (grill-then-plan), debugging (debug-mantra → post-mortem), review (scrutinize,
  dual-verifier), system study (study-design-verify, fit-gap-analysis, naming-audit,
  drive-to-legacy, ticket-trace), and communication (management-talk, invoice-generator,
  problem-description) skills.

**Start here: [PLAYBOOK.md](PLAYBOOK.md)** — the one-page map of when to reach for what.
The only command to memorize is `/daily`.

## Install (each colleague, once)

**Prerequisites:** [Claude Code](https://code.claude.com), **Azure CLI** (`az login`),
**.NET 10 SDK**, **Python 3** + `openpyxl` (`pip install openpyxl`).

```text
# in Claude Code:
/plugin marketplace add ThodsaphonSonthiphin/workflow-daily-work
/plugin install ado-backlog@workflow-daily-work

# then sign in to Azure DevOps and check your setup:
az login
/ado-backlog:setup-check
```

> CLI equivalents: `claude plugin marketplace add ThodsaphonSonthiphin/workflow-daily-work` and
> `claude plugin install ado-backlog@workflow-daily-work`.
> For team-wide install, add `--scope project` (writes to `.claude/settings.json`).

## Use it

```text
/ado-backlog:run "C:\path\to\your-findings.xlsx"
```

Answer the prompts (column mapping, which severities, who to assign to), **approve the
dry-run**, and it creates the work items and writes the ticket links back into your file.
Nothing is created in Azure DevOps until you approve the dry-run.

See [`plugins/ado-backlog/README.md`](plugins/ado-backlog/README.md) for the full toolkit and
[`plugins/ado-backlog/QUICKSTART.md`](plugins/ado-backlog/QUICKSTART.md) for the one-page cheat sheet.

## Repo layout

```
.claude-plugin/marketplace.json        # this marketplace (lists all three plugins)
plugins/ado-backlog/
├── .claude-plugin/plugin.json
├── skills/                            # 7 skills (each invocable as /ado-backlog:<name>)
├── commands/                          # /ado-backlog:run, /ado-backlog:setup-check
├── scripts/                           # create-backlog.cs, read_source.py, tracking.py, setup_check.ps1
├── references/data-contracts.md       # the JSON shapes that connect the steps
├── examples/                          # sample findings + backlog_input
├── README.md
└── QUICKSTART.md
```
