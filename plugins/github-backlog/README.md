# GitHub Backlog Toolkit

Turn findings from any input — spreadsheet, audit doc, pasted list — into a
**GitHub Issues backlog** with labels, a milestone, and a tracking issue. Same
pipeline shape as `ado-backlog`, GitHub-native conventions.

## Install

```
/plugin install github-backlog@workflow-daily-work
```

## Quick start

1. Set your target repo: `$env:GH_OWNER = "MyOrg"` / `$env:GH_REPO = "MyRepo"`
2. Run: `/github-backlog:run path/to/audit.xlsx`
3. Review the dry-run table → approve → issues are created

Full step-by-step: see [QUICKSTART.md](QUICKSTART.md).

## Commands

| Command | What it does |
|---|---|
| `/github-backlog:run [file]` | Full pipeline: extract → triage → classify → create |
| `/github-backlog:my-work` | List your assigned open issues |
| `/github-backlog:setup-check` | Verify prerequisites |
| `/github-backlog:github-auth` | Check / fix GitHub auth |

## Label convention

Flat GitHub-default style, auto-created if missing:

| Dimension | Labels |
|---|---|
| Type | `bug`, `enhancement`, `task`, `documentation` |
| Priority | `P0`, `P1`, `P2`, `P3` |
| Size | `size:XS`, `size:S`, `size:M`, `size:L`, `size:XL` |

## Pipeline

```
extract-findings → triage-findings → classify-github-issues
  → [visual dry-run] → github-create-issues → github-writeback-tracking
```

## Safety

- Never creates issues without the user seeing and approving the full list first
- Write-back requires backing up the source spreadsheet
- Non-idempotent: re-running the real run creates duplicates
