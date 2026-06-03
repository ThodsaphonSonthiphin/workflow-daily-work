# Design Spec — github-backlog plugin

**Date:** 2026-06-02  
**Status:** Draft — awaiting approval  
**Topic:** New `github-backlog` plugin that mirrors the `ado-backlog` pipeline against GitHub Issues

---

## Goal

Add a `github-backlog` plugin to this marketplace that turns findings (audit spreadsheets, docs, pasted lists) into GitHub Issues — using the same pipeline shape as `ado-backlog` but with GitHub-native conventions. A team that only uses GitHub should be able to install one plugin and get the full pipeline.

## Non-goals

- GitHub Projects (kanban/board layer) — out of scope
- Cross-posting to both ADO and GitHub in one run
- Draft issues (GitHub has no draft Issue concept)
- GitHub Enterprise Server URL variations (github.com only in v1)

---

## Install

```
/plugin install github-backlog@workflow-daily-work
```

Registered as a new entry in `.claude-plugin/marketplace.json`, same marketplace as `ado-backlog`.

---

## Plugin structure

```
plugins/github-backlog/
  .claude-plugin/plugin.json
  skills/
    github-auth/SKILL.md
    extract-findings/SKILL.md
    triage-findings/SKILL.md
    classify-github-issues/SKILL.md
    github-create-issues/SKILL.md
    github-writeback-tracking/SKILL.md
    github-my-work/SKILL.md
    findings-to-github-issues/SKILL.md   ← orchestrator
  commands/
    run.md
    my-work.md
    setup-check.md
    github-auth.md
  scripts/
    create_github_issues.py
    setup_check_github.ps1
  references/data-contracts.md
  docs/adr/
  README.md
  QUICKSTART.md
```

Each plugin is self-contained — `extract-findings` and `triage-findings` are duplicated here (same logic as `ado-backlog`) so a GitHub-only install has no dependency on the ADO plugin.

---

## Skill inventory

| Skill | Role | ADO equivalent |
|---|---|---|
| `github-auth` | Verify `gh` CLI / `GH_TOKEN`, confirm owner+repo are reachable | `ado-auth` |
| `extract-findings` | Read source → `findings.json` (identical logic) | `extract-findings` |
| `triage-findings` | Filter to the wave worth creating (identical logic) | `triage-findings` |
| `classify-github-issues` | Map findings to GitHub Issues with labels/milestone | `classify-work-items` |
| `github-create-issues` | Visual dry-run + real run via `create_github_issues.py` | `ado-create-work-items` |
| `github-writeback-tracking` | Write issue numbers/URLs back to source spreadsheet | `ado-writeback-tracking` |
| `github-my-work` | List assigned open issues for the authenticated user | `my-work` |
| `findings-to-github-issues` | Orchestrator — sequences all steps + safety gates | `findings-to-ado-backlog` |

---

## Auth — `github-auth`

Two methods, pick A unless the user has a reason for B.

**Method A — `gh` CLI (recommended)**  
Mirrors the `az` / Entra approach in `ado-auth`. `gh auth token` returns a ready token. Zero config for users who already have `gh` installed and authenticated.

```powershell
gh auth status          # confirm logged in
$token = gh auth token  # get the token
```

**Method B — PAT env var (fallback)**  
Classic or fine-grained PAT. Must have **Issues (Read & Write)** scope.

```powershell
$env:GH_TOKEN = "<your-pat>"
```

`create_github_issues.py` reads `GH_TOKEN` automatically; if unset it shells out to `gh auth token`.

**Target repo** is specified via env vars (bare names, not URLs):

```powershell
$env:GH_OWNER = "Cartagena365"   # org or user name
$env:GH_REPO  = "GlassHull"     # repo name
```

**Verify** (confirms token + repo are reachable):

```powershell
gh api repos/$env:GH_OWNER/$env:GH_REPO --jq '.full_name'
```

A clean result proves auth AND that the repo exists.

---

## Label convention

GitHub's own default style — flat, no prefix, familiar on any repo.

| Dimension | Labels |
|---|---|
| Type | `bug`, `enhancement`, `task`, `documentation` |
| Priority | `P0`, `P1`, `P2`, `P3` |
| Size/estimate | `size:XS`, `size:S`, `size:M`, `size:L`, `size:XL` |

`classify-github-issues` creates any missing labels in the target repo (via `gh label create`) before creating issues — so the pipeline is self-provisioning for labels.

**Epic / parent grouping:** a **milestone** holds the batch (e.g. `Audit Wave 1`). A **tracking issue** is created first with a task list (`- [ ] #N <title>`) linking all created issues. GitHub renders this as a progress bar.

**Estimate → size label mapping:**

| Hours | Label |
|---|---|
| ≤ 2h | `size:XS` |
| 3–4h | `size:S` |
| 5–8h | `size:M` |
| 9–16h | `size:L` |
| > 16h | `size:XL` |

The raw hour estimate is also written into the issue body (`**Estimate:** Xh`) so it survives label changes.

---

## Data contracts

`findings.json` is **identical** to `ado-backlog` — the extract/triage steps are backend-agnostic. Two new contracts replace the ADO-specific ones:

### `github_backlog_input.json`

```json
{
  "owner": "Cartagena365",
  "repo":  "GlassHull",
  "milestone": "Audit Wave 1",
  "items": [
    {
      "key":       "row-12",
      "title":     "Fix null check in login handler",
      "body":      "## Finding\n...\n\n**Estimate:** 4h",
      "labels":    ["bug", "P1", "size:S"],
      "assignees": ["pon-username"],
      "milestone": "Audit Wave 1"
    }
  ]
}
```

### `github_backlog_result.json`

```json
{
  "tracking_issue": { "number": 42, "url": "https://github.com/..." },
  "items": [
    {
      "key":    "row-12",
      "number": 43,
      "url":    "https://github.com/Cartagena365/GlassHull/issues/43",
      "status": "created"
    }
  ]
}
```

Canonical shapes live in `plugins/github-backlog/references/data-contracts.md`.

---

## Pipeline steps (orchestrator)

### 0. Prereqs + auth

```powershell
powershell -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check_github.ps1"
```

Checks: `gh` CLI installed + authenticated, Python + requests, `GH_OWNER` / `GH_REPO` set, repo reachable.

### 1. Extract → `findings.json`

Identical to `ado-backlog`. Delegate to **extract-findings**.

### 2. Triage → scoped subset

Identical to `ado-backlog`. Delegate to **triage-findings**. Recommend Critical + confirmed first.

### 3. Classify → `github_backlog_input.json`

Delegate to **classify-github-issues**. It:
- Maps each finding to a title, body, labels (type + priority + size), and assignee
- Proposes a milestone name for the batch
- Shows an estimates table (key → size label → raw hours) and waits for user OK before proceeding

> **GATE — estimates.** Show the table and get approval / adjustments before the dry run.

### 4. Visual dry-run → nothing created

Delegate to **github-create-issues** in dry-run mode. It renders `github_backlog_input.json` as a formatted table:

```
 # | Key    | Title                          | Labels          | Assignee
---|--------|--------------------------------|-----------------|----------
 1 | row-12 | Fix null check in login handler | bug, P1, size:S | pon
 2 | row-15 | Add rate limiting to API        | enhancement, P2 | —
...
Milestone: Audit Wave 1
Tracking issue: yes
```

> **GATE — stop here.** Do not proceed until the user explicitly approves the list.

### 5. Real run → `github_backlog_result.json`

```powershell
python "${CLAUDE_PLUGIN_ROOT}/scripts/create_github_issues.py" `
  --input "<workdir>/github_backlog_input.json" `
  --output "<workdir>/github_backlog_result.json"
```

Script flow:
1. Create or find the milestone
2. Ensure all labels exist (create missing ones)
3. Create each issue — captures `number` and `url` per `key`
4. Create the tracking issue last (all issue numbers now known)
5. Write `github_backlog_result.json`

### 6. Write-back tracking — spreadsheets only

Delegate to **github-writeback-tracking** → adapted `tracking.py` that writes `Issue #` and `Issue URL` columns back to the source spreadsheet. Same idempotent approach as ADO write-back.

> **GATE — back up the source first.**

### 7. Report back

Summary: created count + clickable links, tracking issue link, held/skipped items, follow-up wave.

---

## Safety gates (identical to ado-backlog)

1. **Visual dry-run before real run** — step 4 always precedes step 5
2. **Explicit user approval before any write** — never skip from classification to creation
3. **Back up the source before write-back** — step 6 edits the file in place

---

## `github-my-work`

Standalone skill (outside the pipeline) that lists the authenticated user's **assigned open issues** across the target repo, grouped by priority label.

```powershell
gh issue list --repo "$env:GH_OWNER/$env:GH_REPO" --assignee @me --state open
```

---

## Documentation — QUICKSTART.md structure

Step-by-step guide covering:

1. **Install** — `/plugin install github-backlog@workflow-daily-work`
2. **Prerequisites** — install `gh` CLI, run `gh auth login`, set `GH_OWNER` / `GH_REPO`
3. **Run setup check** — `/github-backlog:setup-check`
4. **Prepare your source** — what inputs work (xlsx, csv, doc, pasted list)
5. **Run the pipeline** — `/github-backlog:run` (one command, full flow)
6. **Review the dry-run table** — what to check before approving
7. **Approve and create** — typing `yes` / `go ahead`
8. **Write-back** — updating the spreadsheet with issue numbers
9. **Check your work** — `/github-backlog:my-work`
10. **Troubleshooting** — common auth errors, label creation failures, milestone conflicts

---

## CONTEXT.md additions

New terms to add:

- **GitHub Owner** — the org or user name segment of a GitHub repo URL (e.g. `Cartagena365`). Carried as `GH_OWNER`. Not a URL.
- **GitHub Repo** — the repository name (e.g. `GlassHull`). Carried as `GH_REPO`.
- **Tracking Issue** — a GitHub Issue whose body contains a task list (`- [ ] #N`) linking all issues in a batch. Renders as a progress bar. The GitHub equivalent of an ADO Feature/Epic parent.
- **Size label** — a `size:XS/S/M/L/XL` label encoding the effort estimate on a GitHub Issue.

---

## marketplace.json change

Add one entry under `"plugins"`:

```json
{
  "name": "github-backlog",
  "path": "plugins/github-backlog",
  "version": "0.1.0"
}
```

Version in `plugins/github-backlog/.claude-plugin/plugin.json` must match.
