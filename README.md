# Workflow Daily Work — Claude Code marketplace

A Claude Code **plugin marketplace** for daily-work automation. It currently ships:

- **`ado-backlog`** — turn findings from any input into an **Azure DevOps backlog** with a
  dry-run + approval gate.
- **`github-backlog`** — turn findings from any input into a **GitHub Issues backlog** with a
  visual dry-run + approval gate.
- **`dev-workflows`** — reusable development workflow skills like `grill-then-plan`,
  `problem-description`, and `management-talk`.

## Install (each colleague, once)

**Prerequisite:** [Claude Code](https://code.claude.com). Additional requirements depend
on the plugin you install (for example `ado-backlog` needs Azure CLI, .NET 10 SDK, and
Python 3 + `openpyxl`; see each plugin README for details).

```text
# in Claude Code:
/plugin marketplace add ThodsaphonSonthiphin/workflow-daily-work
/plugin install ado-backlog@workflow-daily-work
/plugin install github-backlog@workflow-daily-work
/plugin install dev-workflows@workflow-daily-work

# if you use ADO Backlog:
az login
/ado-backlog:setup-check

# if you use GitHub Backlog:
/github-backlog:setup-check
```

> CLI equivalents: `claude plugin marketplace add ThodsaphonSonthiphin/workflow-daily-work`,
> `claude plugin install ado-backlog@workflow-daily-work`,
> `claude plugin install github-backlog@workflow-daily-work`, and
> `claude plugin install dev-workflows@workflow-daily-work`.
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
For the other plugins, see
[`plugins/github-backlog/README.md`](plugins/github-backlog/README.md) and
[`plugins/dev-workflows/README.md`](plugins/dev-workflows/README.md).

## Repo layout

```
.claude-plugin/marketplace.json        # this marketplace (lists all plugins)
plugins/
├── ado-backlog/                       # Azure DevOps backlog pipeline plugin
├── github-backlog/                    # GitHub Issues backlog pipeline plugin
└── dev-workflows/                     # General development workflow skills
```
