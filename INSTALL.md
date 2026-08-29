# Installing workflow-daily-work

There are two ways in. They are alternatives, not steps — pick one. Installing both
leaves you with two copies of every skill.

## Two ways to install

| | plugin channel | npx channel |
|---|---|---|
| the command | `/plugin install dev-workflows@workflow-daily-work` | `npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --all` |
| the unit | a whole plugin | one skill, or all of them |
| who owns the files | Claude Code — a managed, read-only bundle | you — plain files you can read and edit |
| updates | automatic | explicit: `npx skills@latest update <name>` |
| commands and hooks | yes | **no** — skills only |
| short aliases (`/ask`, `/feynman`) | yes | **no** — you type the skill's own name |
| other agents | Claude Code and Antigravity | every agent skills.sh supports |

Take the plugin channel if you want the whole toolkit and never want to think about it
again. Take the npx channel if you want one skill in an unrelated project, or you want to
read and change what the skill actually says.

## The flag that installs everything by accident

Measured 2026-08-29 against this repo:

```text
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill=wait-what   # installs ALL of them
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill wait-what   # installs one
```

The only difference is the `=`. This is the CLI's own argument parsing, not something
this repo can change — and `--skill=<name>` is the form the wider ecosystem's
documentation shows, which is why it is worth calling out. Write the flag with a space.

When you do mean everything, say so with `--all`. Without either flag the CLI opens an
interactive picker, which is fine by hand and unhelpful in a script.

## Command names

Short aliases live in the plugin channel. Through npx you type the skill's own name:

| plugin channel | npx channel |
|---|---|
| `/dev-workflows:ask` | `/asking-to-understand` |
| `/dev-workflows:feynman` | `/feynman-explain` |
| `/dev-workflows:daily` | `/daily` |
| `/dev-workflows:sa-doc` | `/sa-doc` |
| `/dev-workflows:career-growth` | `/career-growth` |
| `/dev-workflows:verify-then-advise` | `/verify-then-advise` |
| `/dev-workflows:wait-what` | `/wait-what` |
| `/decision-map:chart` | `/chart-map` |
| `/decision-map:work` | `/work-map` |
| `/ado-backlog:run` | `/findings-to-ado-backlog` |
| `/ado-backlog:my-work` | `/my-work` |
| `/ado-backlog:setup-check` | `/ado-auth` |
| `/github-backlog:run` | `/findings-to-github-issues` |
| `/github-backlog:my-work` | `/github-my-work` |
| `/github-backlog:github-auth` | `/github-auth` |
| `/github-backlog:setup-check` | `/github-auth` |

A skill installed at `.claude/skills/<name>/` is invocable as `/<name>`. Where a skill
sets `disable-model-invocation: true`, that stops Claude reaching for it on its own — it
never stops you typing it.

## What the npx channel does not carry

- **No hooks.** Nothing is wired into session start. Every skill still works; nothing
  happens automatically.
- **No short aliases.** See the table above.
- **No automatic updates.** Run `npx skills@latest update <name>` when you want a newer
  version. Nothing tells you one exists.
- **No commands directory.** The CLI installs skills and only skills.

## Renamed skills

Two skills in the GitHub pipeline were renamed so they stop colliding with their Azure
DevOps twins:

| old | new |
|---|---|
| `extract-findings` (GitHub) | `github-extract-findings` |
| `triage-findings` (GitHub) | `github-triage-findings` |

The Azure DevOps skills keep the short names. If you installed the GitHub pair under the
old names, remove and re-add them:

```text
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill github-extract-findings
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill github-triage-findings
```

## Machine setup, either way

Installing the skill is not the same as being able to run it. These are once per machine:

| you installed | do this | check it |
|---|---|---|
| anything from `dev-workflows` | Python 3 on PATH. Several skills hand off to the upstream `superpowers` plugin at plan-execution time: `/plugin marketplace add anthropics/claude-plugins-official` then `/plugin install superpowers@claude-plugins-official`. | ask for a plan and confirm the handoff lands |
| anything from `ado-backlog` | `pip install openpyxl`, `az login`, and set `AZDO_ORG` / `AZDO_PROJECT` to **bare names** (`Cartagena365`, `GlassHull`) — not URLs. `AZDO_PAT` is the fallback when Entra tokens are unavailable. | `/ado-auth` |
| anything from `github-backlog` | `pip install openpyxl`, `gh auth login`, and set `GH_OWNER` / `GH_REPO`. | `/github-auth` |

The `setup-check` commands are plugin-channel only. Through npx, `/ado-auth` and
`/github-auth` check your credentials, not the full prerequisite sweep — for that, run
the script bundled with the same skill:

```text
powershell -ExecutionPolicy Bypass -File "${CLAUDE_SKILL_DIR}/scripts/setup_check.ps1"
powershell -ExecutionPolicy Bypass -File "${CLAUDE_SKILL_DIR}/scripts/setup_check_github.ps1"
```
