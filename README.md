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
  problem-description) skills. **Also installable on Google Antigravity** — see
  [dev-workflows on Antigravity](#dev-workflows-on-antigravity).

**Start here: [PLAYBOOK.md](PLAYBOOK.md)** — the one-page map of when to reach for what.
The only command to memorize is `/daily`.

## Install (each colleague, once)

**Prerequisites:** [Claude Code](https://code.claude.com), **Azure CLI** (`az login`),
**.NET 10 SDK**, **Python 3** + `openpyxl` (`pip install openpyxl`).

```text
# in Claude Code:
/plugin marketplace add ThodsaphonSonthiphin/workflow-daily-work
/plugin install ado-backlog@workflow-daily-work
/plugin install github-backlog@workflow-daily-work
/plugin install dev-workflows@workflow-daily-work

# then sign in to Azure DevOps and check your setup:
az login
/ado-backlog:setup-check
```

> CLI equivalents: `claude plugin marketplace add ThodsaphonSonthiphin/workflow-daily-work` and
> `claude plugin install ado-backlog@workflow-daily-work`.
> For team-wide install, add `--scope project` (writes to `.claude/settings.json`).
> Installing mid-session? run `/reload-plugins` to activate without restarting.

### dev-workflows on Antigravity

The `dev-workflows` skills also run on **Google Antigravity** (IDE or CLI). Antigravity
does not read the Claude Code marketplace and resolves bundled-file paths *relative to each
skill directory* (no `${CLAUDE_PLUGIN_ROOT}` expansion), so install via the bundled script:
it stages the skills into Antigravity's skills directory and rewrites those paths to
absolute. **The source tree stays Claude-native, so the marketplace install above is
unaffected.**

**Prerequisites:** `git`, **Python 3.9+**, and Antigravity installed.

```bash
git clone https://github.com/ThodsaphonSonthiphin/workflow-daily-work.git
cd workflow-daily-work/plugins/dev-workflows/.antigravity
python install-antigravity.py          # default: ~/.gemini/config/skills  (IDE global)
# --scope cli                          ->  ~/.gemini/antigravity-cli/skills
# --scope project --project <repo>     ->  <repo>/.agents/skills
```

Then **reload Antigravity** so it rediscovers the skills. A clean run ends with
`rewrote N ${CLAUDE_PLUGIN_ROOT} reference(s)` and no warning (the exact count isn't
load-bearing). Verify the staged script runs:

```bash
python "$HOME/.gemini/config/skills/.dev-workflows-shared/scripts/daily-state.py" --help
```

- Only `dev-workflows` ships an Antigravity installer; `ado-backlog` / `github-backlog`
  are Claude-Code-only for now.
- `grill-then-plan` hands off to `superpowers:writing-plans`, so it also needs a
  **superpowers skills port** installed on Antigravity.
- Whether skills trigger live in the Antigravity IDE must be confirmed on your own
  machine. Details: [`plugins/dev-workflows/.antigravity/INSTALL.md`](plugins/dev-workflows/.antigravity/INSTALL.md).

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
├── skills/                            # 8 skills (each invocable as /ado-backlog:<name>)
├── commands/                          # /ado-backlog:run, /ado-backlog:setup-check, /ado-backlog:my-work
├── scripts/                           # create-backlog.cs, read_source.py, tracking.py, setup_check.ps1
├── references/data-contracts.md       # the JSON shapes that connect the steps
├── examples/                          # sample findings + backlog_input
├── README.md
└── QUICKSTART.md
scripts/sync-personal-skills.ps1       # mirror dev-workflows skills into ~/.claude/skills
```

## Maintaining a personal `~/.claude/skills/` mirror (optional)

If you keep dev-workflows skills as personal copies under `~/.claude/skills/`
(instead of, or alongside, the marketplace install), run the sync after pulling.
It mirrors each skill you already have personally and rewrites the
`${CLAUDE_PLUGIN_ROOT}/...` references to their personal paths so they resolve
(e.g. `${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md` →
`~/.claude/skills/diagram-convention.md`):

```text
pwsh ./scripts/sync-personal-skills.ps1            # sync
pwsh ./scripts/sync-personal-skills.ps1 -DryRun    # preview, write nothing
```

It only touches skills that exist in **both** the repo and your personal dir,
never adds or removes skills sourced from other plugins, and is idempotent.
