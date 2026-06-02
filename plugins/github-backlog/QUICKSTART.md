# GitHub Backlog Toolkit — Quick Start

This guide walks you through turning a findings source into GitHub Issues, step by step.

---

## Step 1: Install the plugin

```
/plugin install github-backlog@workflow-daily-work
```

---

## Step 2: Prerequisites

Install the [GitHub CLI](https://cli.github.com) and log in:

```powershell
gh auth login
```

Install Python dependencies (if not already present):

```powershell
pip install requests openpyxl
```

---

## Step 3: Set your target repo

Set these in your shell before running the pipeline. These are the **bare name** and **repo name** — not URLs:

```powershell
$env:GH_OWNER = "Cartagena365"   # org or user name
$env:GH_REPO  = "GlassHull"     # repository name
```

---

## Step 4: Run the setup check

Confirm everything is in place before investing time in extraction:

```
/github-backlog:setup-check
```

All checks should show PASS. WARN on env vars is fine if you've already set them in the previous step. Fix any FAIL before continuing.

---

## Step 5: Prepare your source

The pipeline accepts any of these:
- **Excel / CSV** (`.xlsx`, `.csv`, `.tsv`) — one finding per row
- **Word / Markdown / PDF** — Claude reads it directly
- **Pasted text** — paste it into the chat

No special format required. Claude maps your columns to the standard schema and confirms the mapping with you before proceeding.

---

## Step 6: Run the pipeline

```
/github-backlog:run path/to/your/audit.xlsx
```

Or paste text directly and type `/github-backlog:run`.

Claude will:
1. Extract findings → `findings.json`
2. Show you the finding counts and confirm the column mapping
3. Recommend a wave (Critical + confirmed first) and ask for your OK
4. Map findings to labels, milestone, and body → `github_backlog_input.json`
5. Show you an estimates table (size labels) — you can adjust before continuing

---

## Step 7: Review the dry-run table

Before creating anything, Claude shows you a table of every issue that *would* be created:

```
 # | Key    | Title                              | Labels               | Assignee
---|--------|------------------------------------|----------------------|---------
 1 | row-1  | Portal label "Auto" should show... | bug, P1, size:S      | —
 2 | row-2  | Add rate limiting to API           | enhancement, P2, M   | pon
...
Milestone: Audit Wave 1
Tracking issue: yes
Total: 2 issues
```

Check:
- Titles are specific and self-contained
- Labels look right (type, priority, size)
- Milestone name is what you want
- Assignees are correct (or blank if unassigned is fine)

If anything is wrong, say what to change and Claude will update the JSON and re-render.

---

## Step 8: Approve and create

When the table looks right, say **"go ahead"** or **"create them"**.

Claude runs `create_github_issues.py`, which:
1. Creates any missing labels
2. Creates (or finds) the milestone
3. Creates each issue
4. Creates a tracking issue with a task list linking all issues

You'll see output like:
```
  key row-1 -> #43 https://github.com/Cartagena365/GlassHull/issues/43
  key row-2 -> #44 https://github.com/Cartagena365/GlassHull/issues/44
  tracking issue -> #45 https://github.com/Cartagena365/GlassHull/issues/45
```

---

## Step 9: Write-back (spreadsheets only)

If your source was a spreadsheet, write the issue numbers and URLs back to it so every source row shows which issue it became.

Claude will ask you to back up the file first:

```powershell
Copy-Item "audit.xlsx" "audit.bak.xlsx"
```

Then it runs `github_tracking.py` to stamp `Issue #`, `Issue URL`, `State`, `Created` columns onto matching rows.

---

## Step 10: Check your work

```
/github-backlog:my-work
```

Lists your assigned open issues, P0 first. The top item is your highest-priority actionable work.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `gh: not logged in` | Run `gh auth login` |
| `HTTP 401` | Token expired — re-run `gh auth login` or check `GH_TOKEN` |
| `HTTP 403` | PAT scope missing Issues Read & Write — reissue the PAT |
| Repo not found / 404 | Check `GH_OWNER` / `GH_REPO` spelling; confirm repo exists |
| Labels not created | Confirm your token has write access to the repo |
| Milestone conflict | If a milestone with that name already exists (closed), the script finds the open one or creates a new one |
| `warn: key X not found in source` | The `--key` column name doesn't match; re-check which column was used as `key` in extraction |
| Duplicate issues created | Don't re-run the real run on the same input — prune the JSON to un-filed keys first |
