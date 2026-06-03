# github-backlog Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `github-backlog` plugin that turns findings from any source into GitHub Issues, mirroring the `ado-backlog` pipeline shape with GitHub-native conventions.

**Architecture:** Self-contained plugin under `plugins/github-backlog/` registered in the marketplace. Pipeline: extract → triage → classify → visual-dry-run → create (Python + GitHub REST API) → writeback. Eight SKILL.md files; three Python/PowerShell scripts.

**Tech Stack:** Python 3 (`requests`, `openpyxl`), PowerShell 5.1, `gh` CLI, GitHub REST API v2022-11-28, markdown SKILL.md files.

---

## File map

| Status | File | What it does |
|---|---|---|
| Create | `plugins/github-backlog/.claude-plugin/plugin.json` | Plugin manifest |
| Modify | `.claude-plugin/marketplace.json` | Register new plugin |
| Create | `plugins/github-backlog/references/data-contracts.md` | Canonical JSON schemas |
| Create | `plugins/github-backlog/scripts/setup_check_github.ps1` | Prereq checker |
| Create | `plugins/github-backlog/scripts/create_github_issues.py` | Issue creation script |
| Create | `plugins/github-backlog/scripts/github_tracking.py` | Write-back script |
| Create | `plugins/github-backlog/skills/github-auth/SKILL.md` | Auth skill |
| Create | `plugins/github-backlog/skills/extract-findings/SKILL.md` | Extract skill |
| Create | `plugins/github-backlog/skills/triage-findings/SKILL.md` | Triage skill |
| Create | `plugins/github-backlog/skills/classify-github-issues/SKILL.md` | Classify skill |
| Create | `plugins/github-backlog/skills/github-create-issues/SKILL.md` | Create skill |
| Create | `plugins/github-backlog/skills/github-writeback-tracking/SKILL.md` | Write-back skill |
| Create | `plugins/github-backlog/skills/github-my-work/SKILL.md` | My-work skill |
| Create | `plugins/github-backlog/skills/findings-to-github-issues/SKILL.md` | Orchestrator |
| Create | `plugins/github-backlog/commands/run.md` | `/github-backlog:run` |
| Create | `plugins/github-backlog/commands/my-work.md` | `/github-backlog:my-work` |
| Create | `plugins/github-backlog/commands/setup-check.md` | `/github-backlog:setup-check` |
| Create | `plugins/github-backlog/commands/github-auth.md` | `/github-backlog:github-auth` |
| Create | `plugins/github-backlog/README.md` | User overview |
| Create | `plugins/github-backlog/QUICKSTART.md` | Step-by-step guide |

---

## Task 1: Plugin scaffold + marketplace registration

**Files:**
- Create: `plugins/github-backlog/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Create plugin.json**

```json
{
  "name": "github-backlog",
  "displayName": "GitHub Backlog Toolkit",
  "version": "0.1.0",
  "description": "Turn findings from any input into GitHub Issues: extract -> triage -> classify (labels + milestone) -> visual dry-run -> create -> write issue links back. Composable: each step is its own skill, plus a one-shot orchestrator.",
  "author": {
    "name": "ThodsaphonSonthiphin",
    "email": "thodsaphon.sonthipin@cartagena.no",
    "url": "https://github.com/ThodsaphonSonthiphin"
  },
  "homepage": "https://github.com/ThodsaphonSonthiphin/workflow-daily-work",
  "repository": "https://github.com/ThodsaphonSonthiphin/workflow-daily-work",
  "license": "MIT",
  "keywords": ["github", "issues", "backlog", "work-items", "triage", "spreadsheet", "daily-work"]
}
```

Write to: `plugins/github-backlog/.claude-plugin/plugin.json`

- [ ] **Step 2: Register in marketplace.json**

In `.claude-plugin/marketplace.json`, add a new entry inside the `"plugins"` array after the `dev-workflows` entry:

```json
{
  "name": "github-backlog",
  "source": "./plugins/github-backlog",
  "description": "Turn findings from any input (spreadsheet, doc, pasted text) into GitHub Issues: extract, triage, classify by labels and milestone, visual dry-run, create with an approval gate, and write issue links back to the source.",
  "version": "0.1.0",
  "author": {
    "name": "ThodsaphonSonthiphin",
    "url": "https://github.com/ThodsaphonSonthiphin"
  },
  "homepage": "https://github.com/ThodsaphonSonthiphin/workflow-daily-work",
  "repository": "https://github.com/ThodsaphonSonthiphin/workflow-daily-work",
  "license": "MIT",
  "category": "development",
  "keywords": ["github", "issues", "backlog", "work-items", "triage"]
}
```

- [ ] **Step 3: Verify version sync**

The `version` field in `plugin.json` and the marketplace entry must both be `"0.1.0"`. Read both files and confirm they match.

- [ ] **Step 4: Commit**

```bash
git add plugins/github-backlog/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "feat(github-backlog): scaffold plugin manifest and marketplace entry"
```

---

## Task 2: Data contracts

**Files:**
- Create: `plugins/github-backlog/references/data-contracts.md`

- [ ] **Step 1: Write data-contracts.md**

```markdown
# Data contracts (github-backlog)

Three JSON shapes connect the pipeline steps. Keep them stable — the bundled
scripts depend on these exact field names.

```
extract-findings          -> findings.json              (backend-agnostic)
classify-github-issues    -> github_backlog_input.json  (consumed by create_github_issues.py)
github-create-issues      -> github_backlog_result.json (consumed by github_tracking.py)
```

The link between a source row and its created issue is the **`key`** field — carried
through all three files so issue links can be written back to the right row.

---

## 1. `findings.json` — identical to ado-backlog

```json
{
  "source": "Downloads/CRM_Audit.xlsx (sheet 'Findings')",
  "keyColumn": "#",
  "findings": [
    {
      "key": "1",
      "section": "Login",
      "current": "Auto",
      "expected": "Automotive Cargo",
      "kind": "rename",
      "severity": "Critical",
      "status": "confirmed",
      "recommendation": "Rename label",
      "notes": "Appears on 3 screens."
    }
  ]
}
```

| field | required | notes |
|---|---|---|
| `key` | yes | Stable id per finding. Used for write-back. |
| `current` / `expected` | yes | Observed vs canonical value. |
| `kind` | no | `rename` \| `disambiguation` \| `missing` \| `other`. |
| `severity` | no | `Critical` \| `High` \| `Medium` \| `Low`. Drives priority label. |
| `status` | no | Free text (`confirmed`, `needs-review`). Triage filter. |
| `section` / `recommendation` / `notes` | no | Carried into issue body. |

---

## 2. `github_backlog_input.json` — issues to create

```json
{
  "owner": "Cartagena365",
  "repo": "GlassHull",
  "milestone": "Audit Wave 1",
  "items": [
    {
      "key": "1",
      "title": "Portal label \"Auto\" should display \"Automotive Cargo\"",
      "body": "## Finding\n\n**Current:** Auto  \n**Expected:** Automotive Cargo  \n**Recommendation:** Rename label on all screens.\n\n**Estimate:** 2h",
      "labels": ["bug", "P1", "size:XS"],
      "assignees": [],
      "milestone": "Audit Wave 1"
    }
  ]
}
```

| field | required | notes |
|---|---|---|
| `owner` / `repo` | yes* | *Overridden by `GH_OWNER` / `GH_REPO` env vars if set. |
| `milestone` | yes | Name of the batch milestone. Created if it doesn't exist. |
| `items[].key` | yes | Threads back to `findings.json` and into the result. |
| `items[].title` | yes | Issue title. Self-contained — readable without opening. |
| `items[].body` | yes | Markdown. Include `**Estimate:** Xh` at the end. |
| `items[].labels` | yes | Flat GitHub labels: type (`bug`/`enhancement`/`task`/`documentation`), priority (`P0`-`P3`), size (`size:XS`-`size:XL`). |
| `items[].assignees` | no | GitHub usernames. Empty array = unassigned. |

**Label convention:**

| Dimension | Labels |
|---|---|
| Type | `bug`, `enhancement`, `task`, `documentation` |
| Priority | `P0`, `P1`, `P2`, `P3` |
| Size/estimate | `size:XS` (≤2h), `size:S` (3-4h), `size:M` (5-8h), `size:L` (9-16h), `size:XL` (>16h) |

Missing labels are auto-created by `create_github_issues.py` before the first issue.

---

## 3. `github_backlog_result.json` — what got created

```json
{
  "owner": "Cartagena365",
  "repo": "GlassHull",
  "tracking_issue": {
    "number": 42,
    "url": "https://github.com/Cartagena365/GlassHull/issues/42"
  },
  "items": [
    {
      "key": "1",
      "number": 43,
      "url": "https://github.com/Cartagena365/GlassHull/issues/43",
      "status": "created",
      "title": "Portal label \"Auto\" should display \"Automotive Cargo\""
    }
  ]
}
```

`github_tracking.py writeback` matches each result `key` to the source's key column
and writes `Issue #` / `Issue URL` / `State` / `Created`.
```

Write to: `plugins/github-backlog/references/data-contracts.md`

- [ ] **Step 2: Commit**

```bash
git add plugins/github-backlog/references/data-contracts.md
git commit -m "feat(github-backlog): add data contracts reference"
```

---

## Task 3: setup_check_github.ps1

**Files:**
- Create: `plugins/github-backlog/scripts/setup_check_github.ps1`

- [ ] **Step 1: Write setup_check_github.ps1**

```powershell
# setup_check_github.ps1 — verify prerequisites for the github-backlog pipeline.
# Run: powershell -ExecutionPolicy Bypass -File setup_check_github.ps1
# Prints PASS / WARN / FAIL with a fix for anything missing. Read-only; changes nothing.

$ok = $true
function Line($status, $what, $detail) {
    $color = switch ($status) { "PASS" { "Green" } "WARN" { "Yellow" } default { "Red" } }
    Write-Host ("{0,-5} {1,-22} {2}" -f $status, $what, $detail) -ForegroundColor $color
}

# --- gh CLI present + logged in ---
$gh = (Get-Command gh -ErrorAction SilentlyContinue)
if (-not $gh) {
    Line "FAIL" "gh CLI" "not found. Install: https://cli.github.com"; $ok = $false
} else {
    $ver = (gh --version | Select-Object -First 1)
    Line "PASS" "gh CLI" $ver
    $authOut = gh auth status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Line "PASS" "gh auth" "logged in"
    } else {
        Line "FAIL" "gh auth" "not logged in. Run: gh auth login"; $ok = $false
    }
}

# --- Python ---
$py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) {
    Line "FAIL" "Python" "not found. Install Python 3.x"; $ok = $false
} else {
    $v = python --version 2>&1
    Line "PASS" "Python" "$v"

    # requests
    $req = python -c "import requests; print(requests.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Line "PASS" "requests" "$req"
    } else {
        Line "FAIL" "requests" "not installed. Run: pip install requests"; $ok = $false
    }

    # openpyxl (for write-back)
    $xl = python -c "import openpyxl; print(openpyxl.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Line "PASS" "openpyxl" "$xl"
    } else {
        Line "FAIL" "openpyxl" "not installed. Run: pip install openpyxl"; $ok = $false
    }
}

# --- Env vars ---
if ($env:GH_OWNER) {
    Line "PASS" "GH_OWNER" $env:GH_OWNER
} else {
    Line "WARN" "GH_OWNER" "not set — set before running the pipeline"
}
if ($env:GH_REPO) {
    Line "PASS" "GH_REPO" $env:GH_REPO
} else {
    Line "WARN" "GH_REPO" "not set — set before running the pipeline"
}

# --- Repo reachable (only if both env vars set) ---
if ($env:GH_OWNER -and $env:GH_REPO) {
    $full = gh api "repos/$env:GH_OWNER/$env:GH_REPO" --jq '.full_name' 2>&1
    if ($LASTEXITCODE -eq 0) {
        Line "PASS" "repo reachable" $full
    } else {
        Line "FAIL" "repo reachable" "could not reach $env:GH_OWNER/$env:GH_REPO — check spelling and permissions"
        $ok = $false
    }
}

Write-Host ""
if ($ok) { Write-Host "All checks passed." -ForegroundColor Green }
else      { Write-Host "Some checks failed — fix them before running the pipeline." -ForegroundColor Red }
```

Write to: `plugins/github-backlog/scripts/setup_check_github.ps1`

- [ ] **Step 2: Smoke-test the script**

```powershell
powershell -ExecutionPolicy Bypass -File "plugins/github-backlog/scripts/setup_check_github.ps1"
```

Expected: PASS for gh CLI, Python, requests, openpyxl if your machine has them. WARN for GH_OWNER/GH_REPO if not set (warnings are OK — they are not pre-set). No red FAIL lines unless something is genuinely missing.

- [ ] **Step 3: Commit**

```bash
git add plugins/github-backlog/scripts/setup_check_github.ps1
git commit -m "feat(github-backlog): add setup_check_github.ps1"
```

---

## Task 4: create_github_issues.py

**Files:**
- Create: `plugins/github-backlog/scripts/create_github_issues.py`

- [ ] **Step 1: Write create_github_issues.py**

```python
#!/usr/bin/env python3
"""
create_github_issues.py — create GitHub Issues from github_backlog_input.json.

Usage:
    python create_github_issues.py --input <path> --output <path>

Auth:  reads GH_TOKEN env var first; falls back to `gh auth token`.
Target: GH_OWNER + GH_REPO env vars override owner/repo from the input JSON.
"""
import argparse
import json
import os
import subprocess
import sys

import requests

API = "https://api.github.com"
HEADERS_BASE = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

LABEL_COLORS = {
    "bug": "d73a4a",
    "enhancement": "a2eeef",
    "task": "e4e669",
    "documentation": "0075ca",
    "tracking": "cccccc",
    "P0": "b60205",
    "P1": "d93f0b",
    "P2": "fbca04",
    "P3": "0e8a16",
    "size:XS": "c5def5",
    "size:S": "bfd4f2",
    "size:M": "d4c5f9",
    "size:L": "e99695",
    "size:XL": "f9d0c4",
}


def get_token():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        sys.exit(f"no token: set GH_TOKEN or run `gh auth login` ({exc})")


def gh(method, path, token, **kwargs):
    resp = requests.request(
        method,
        f"{API}{path}",
        headers={**HEADERS_BASE, "Authorization": f"Bearer {token}"},
        **kwargs,
    )
    if not resp.ok:
        sys.exit(f"GitHub API {method} {path} -> {resp.status_code}: {resp.text}")
    if resp.status_code == 204:
        return {}
    return resp.json()


def ensure_labels(owner, repo, token, needed):
    existing = {l["name"] for l in gh("GET", f"/repos/{owner}/{repo}/labels?per_page=100", token)}
    for name in needed:
        if name not in existing:
            color = LABEL_COLORS.get(name, "ededed")
            gh("POST", f"/repos/{owner}/{repo}/labels", token, json={"name": name, "color": color})
            print(f"  created label: {name}")


def get_or_create_milestone(owner, repo, token, title):
    milestones = gh("GET", f"/repos/{owner}/{repo}/milestones?state=open&per_page=100", token)
    for m in milestones:
        if m["title"] == title:
            return m["number"]
    result = gh("POST", f"/repos/{owner}/{repo}/milestones", token, json={"title": title})
    print(f"  created milestone: {title} (#{result['number']})")
    return result["number"]


def create_issue(owner, repo, token, item, milestone_number):
    payload = {
        "title": item["title"],
        "body": item.get("body", ""),
        "labels": item.get("labels", []),
        "assignees": item.get("assignees", []),
        "milestone": milestone_number,
    }
    result = gh("POST", f"/repos/{owner}/{repo}/issues", token, json=payload)
    return result["number"], result["html_url"]


def create_tracking_issue(owner, repo, token, milestone_title, milestone_number, created_items):
    task_lines = "\n".join(f"- [ ] #{i['number']} {i['title']}" for i in created_items)
    body = f"Tracking issue for **{milestone_title}**.\n\n## Issues\n\n{task_lines}"
    result = gh("POST", f"/repos/{owner}/{repo}/issues", token, json={
        "title": f"[Tracking] {milestone_title}",
        "body": body,
        "labels": ["tracking"],
        "milestone": milestone_number,
    })
    return result["number"], result["html_url"]


def main():
    ap = argparse.ArgumentParser(description="Create GitHub Issues from github_backlog_input.json")
    ap.add_argument("--input", required=True, help="Path to github_backlog_input.json")
    ap.add_argument("--output", required=True, help="Path to write github_backlog_result.json")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        plan = json.load(f)

    owner = os.environ.get("GH_OWNER") or plan.get("owner")
    repo = os.environ.get("GH_REPO") or plan.get("repo")
    if not owner or not repo:
        sys.exit("set GH_OWNER and GH_REPO env vars, or include 'owner'/'repo' in the input JSON")

    token = get_token()
    milestone_title = plan.get("milestone", "Backlog")
    items = plan.get("items", [])

    print(f"repo:      {owner}/{repo}")
    print(f"milestone: {milestone_title}")
    print(f"items:     {len(items)}")

    # Collect all labels needed across all items + tracking label
    all_labels = {"tracking"}
    for item in items:
        all_labels.update(item.get("labels", []))

    ensure_labels(owner, repo, token, all_labels)
    milestone_number = get_or_create_milestone(owner, repo, token, milestone_title)

    result_items = []
    created_for_tracking = []
    for item in items:
        number, url = create_issue(owner, repo, token, item, milestone_number)
        print(f"  key {item['key']} -> #{number} {url}")
        result_items.append({
            "key": item["key"],
            "number": number,
            "url": url,
            "status": "created",
            "title": item["title"],
        })
        created_for_tracking.append({"number": number, "title": item["title"]})

    tracking_number, tracking_url = create_tracking_issue(
        owner, repo, token, milestone_title, milestone_number, created_for_tracking
    )
    print(f"  tracking issue -> #{tracking_number} {tracking_url}")

    result = {
        "owner": owner,
        "repo": repo,
        "tracking_issue": {"number": tracking_number, "url": tracking_url},
        "items": result_items,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
```

Write to: `plugins/github-backlog/scripts/create_github_issues.py`

- [ ] **Step 2: Verify the script parses cleanly**

```powershell
python -c "import ast, sys; ast.parse(open('plugins/github-backlog/scripts/create_github_issues.py').read()); print('syntax OK')"
```

Expected: `syntax OK`

- [ ] **Step 3: Verify --help runs without error**

```powershell
python "plugins/github-backlog/scripts/create_github_issues.py" --help
```

Expected: prints usage with `--input` and `--output` arguments listed.

- [ ] **Step 4: Commit**

```bash
git add plugins/github-backlog/scripts/create_github_issues.py
git commit -m "feat(github-backlog): add create_github_issues.py"
```

---

## Task 5: github_tracking.py

**Files:**
- Create: `plugins/github-backlog/scripts/github_tracking.py`

- [ ] **Step 1: Write github_tracking.py**

```python
"""
github_tracking.py — add traceability columns to a spreadsheet and write created
GitHub issue numbers/URLs back, matched row-by-row by key.

Subcommands:
  add-columns  --source <xlsx|csv> [--key "#"]
      Ensure these columns exist (appended after the last used column, idempotent):
        Issue # | Issue URL | State | Created
  writeback    --source <xlsx|csv> --result <github_backlog_result.json> [--key "#"]
      Match each result item's `key` to the source key column and fill the
      tracking columns. Idempotent: rows that already have an Issue # are left as-is.
"""
import argparse
import json
from datetime import datetime

TRACKING = ["Issue #", "Issue URL", "State", "Created"]


# ---------- xlsx ----------
def _xlsx_headers(ws):
    return {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}


def xlsx_add_columns(path):
    import openpyxl
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    headers = _xlsx_headers(ws)
    missing = [c for c in TRACKING if c not in headers]
    start = ws.max_column + 1
    for i, name in enumerate(missing):
        ws.cell(row=1, column=start + i, value=name)
    wb.save(path)
    cols = _xlsx_headers(ws)
    from openpyxl.utils import get_column_letter
    print("tracking columns: " + ", ".join(f"{n}={get_column_letter(cols[n])}" for n in TRACKING))


def xlsx_writeback(path, result, key_col):
    import openpyxl
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    headers = _xlsx_headers(ws)
    for needed in TRACKING + [key_col]:
        if needed not in headers:
            raise SystemExit(f"missing column '{needed}' — run add-columns first (key='{key_col}')")
    row_of = {}
    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=headers[key_col]).value
        if v is not None:
            row_of[str(v)] = r
    return _do_writeback(result, row_of,
                         setter=lambda r, col, val: ws.cell(row=r, column=headers[col], value=val),
                         saver=lambda: wb.save(path))


# ---------- csv ----------
def csv_load(path):
    import csv
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


def csv_save(path, rows):
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def csv_add_columns(path):
    rows = csv_load(path)
    if not rows:
        raise SystemExit("empty csv")
    header = rows[0]
    for name in TRACKING:
        if name not in header:
            header.append(name)
            for r in rows[1:]:
                r.append("")
    csv_save(path, rows)
    print("tracking columns ensured: " + ", ".join(TRACKING))


def csv_writeback(path, result, key_col):
    rows = csv_load(path)
    header = rows[0]
    idx = {name: i for i, name in enumerate(header)}
    for needed in TRACKING + [key_col]:
        if needed not in idx:
            raise SystemExit(f"missing column '{needed}' — run add-columns first")
    row_of = {str(r[idx[key_col]]): r for r in rows[1:] if len(r) > idx[key_col]}

    def setter(rowobj, col, val):
        rowobj[idx[col]] = val
    return _do_writeback(result, row_of, setter=setter, saver=lambda: csv_save(path, rows))


# ---------- shared ----------
def _do_writeback(result, row_of, setter, saver):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    written = 0
    for item in result.get("items", []):
        if not item.get("number"):
            continue
        target = row_of.get(str(item["key"]))
        if target is None:
            print(f"  warn: key {item['key']} not found in source")
            continue
        setter(target, "Issue #", item["number"])
        setter(target, "Issue URL", item.get("url", ""))
        setter(target, "State", "open")
        setter(target, "Created", stamp)
        written += 1
        print(f"  key {item['key']} -> #{item['number']}")
    saver()
    tracking = result.get("tracking_issue") or {}
    if tracking.get("url"):
        print(f"tracking issue: {tracking['url']}")
    print(f"wrote {written} issue links back to source")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add-columns")
    a.add_argument("--source", required=True)
    a.add_argument("--key", default="#")
    w = sub.add_parser("writeback")
    w.add_argument("--source", required=True)
    w.add_argument("--result", required=True)
    w.add_argument("--key", default="#")
    args = ap.parse_args()

    is_csv = args.source.lower().endswith((".csv", ".tsv"))
    if args.cmd == "add-columns":
        (csv_add_columns if is_csv else xlsx_add_columns)(args.source)
    else:
        with open(args.result, encoding="utf-8") as f:
            result = json.load(f)
        (csv_writeback if is_csv else xlsx_writeback)(args.source, result, args.key)


if __name__ == "__main__":
    main()
```

Write to: `plugins/github-backlog/scripts/github_tracking.py`

- [ ] **Step 2: Verify syntax**

```powershell
python -c "import ast; ast.parse(open('plugins/github-backlog/scripts/github_tracking.py').read()); print('syntax OK')"
```

Expected: `syntax OK`

- [ ] **Step 3: Test add-columns on a scratch CSV**

Create a minimal test CSV and verify `add-columns` appends the four tracking columns:

```powershell
"#,Title,Severity`n1,Fix login bug,Critical`n2,Add rate limit,High" | Out-File -Encoding utf8 "plugins/github-backlog/scripts/test_scratch.csv"
python "plugins/github-backlog/scripts/github_tracking.py" add-columns --source "plugins/github-backlog/scripts/test_scratch.csv" --key "#"
```

Expected output: `tracking columns ensured: Issue #, Issue URL, State, Created`

- [ ] **Step 4: Test writeback on the scratch CSV**

```powershell
@"
{
  "owner": "TestOrg", "repo": "TestRepo",
  "tracking_issue": {"number": 5, "url": "https://github.com/TestOrg/TestRepo/issues/5"},
  "items": [
    {"key": "1", "number": 3, "url": "https://github.com/TestOrg/TestRepo/issues/3", "status": "created", "title": "Fix login bug"},
    {"key": "2", "number": 4, "url": "https://github.com/TestOrg/TestRepo/issues/4", "status": "created", "title": "Add rate limit"}
  ]
}
"@ | Out-File -Encoding utf8 "plugins/github-backlog/scripts/test_result.json"
python "plugins/github-backlog/scripts/github_tracking.py" writeback --source "plugins/github-backlog/scripts/test_scratch.csv" --result "plugins/github-backlog/scripts/test_result.json" --key "#"
```

Expected: `key 1 -> #3`, `key 2 -> #4`, `wrote 2 issue links back to source`. Verify the CSV has `Issue #`, `Issue URL`, `State`, `Created` filled in for both rows.

- [ ] **Step 5: Clean up test files**

```powershell
Remove-Item "plugins/github-backlog/scripts/test_scratch.csv" -ErrorAction SilentlyContinue
Remove-Item "plugins/github-backlog/scripts/test_result.json" -ErrorAction SilentlyContinue
```

- [ ] **Step 6: Commit**

```bash
git add plugins/github-backlog/scripts/github_tracking.py
git commit -m "feat(github-backlog): add github_tracking.py"
```

---

## Task 6: github-auth skill

**Files:**
- Create: `plugins/github-backlog/skills/github-auth/SKILL.md`

- [ ] **Step 1: Write github-auth/SKILL.md**

```markdown
---
name: github-auth
description: >-
  Authenticate to GitHub and fix auth problems — the shared primitive every
  other github-* skill relies on. Use this BEFORE any create/query when GitHub
  auth is uncertain, and whenever a GitHub API call misbehaves: a call returns
  401 or 403, "gh not logged in" / token missing, results come back empty or
  from the wrong repo. Covers the two supported methods (gh CLI via `gh auth
  token`, or GH_TOKEN env var), a one-line PowerShell verify snippet against
  the repo API, and a 401/403/wrong-repo troubleshooting table. Invoke when
  someone says "I'm getting a 401 from GitHub", "github-create-issues says no
  token", "gh auth failing", or "check my GitHub login before we run".
---

# github-auth

Authenticate to GitHub and diagnose auth failures. This is a **verify and
troubleshoot** skill — the bundled `create_github_issues.py` already implements
both auth methods, so you are not writing new auth code here. You are confirming
a token works and the owner/repo point where the user expects, then unblocking
the create/query skills ([[github-create-issues]], [[findings-to-github-issues]]).

GitHub accepts two credential styles. Pick A unless the user has a reason to use a PAT.

## Method A — gh CLI (recommended)

Why preferred: no long-lived secret to store, and it rides the user's existing `gh`
session. `gh auth token` returns a ready-to-use token.

```powershell
gh auth login          # one-time setup
$token = gh auth token # get the current token
```

Use it as a bearer header: `Authorization: Bearer <token>`.

## Method B — Personal Access Token (PAT)

Use when `gh` CLI isn't available (e.g. a service context) or the user has an
existing PAT. Scope must include **Issues (Read & Write)** on the target repo.
Classic PAT or fine-grained PAT both work.

```powershell
$env:GH_TOKEN = "<your-pat>"
```

`create_github_issues.py` reads `GH_TOKEN` automatically; if unset it shells out
to `gh auth token`. So setting (or unsetting) `GH_TOKEN` is how you switch methods.

## Set target repo

```powershell
$env:GH_OWNER = "Cartagena365"   # org or user name — NOT a URL
$env:GH_REPO  = "GlassHull"     # repo name — NOT a URL
```

## Verify the credential works

```powershell
gh api "repos/$env:GH_OWNER/$env:GH_REPO" --jq '.full_name'
```

A clean result (e.g. `Cartagena365/GlassHull`) proves the token is valid AND the
repo exists and is reachable. Anything else, see the troubleshooting table below.

For a broader prereq sweep (gh CLI, Python, requests, openpyxl, env vars) run the
bundled checker — it is read-only and changes nothing:

```powershell
powershell -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check_github.ps1"
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| **HTTP 401** Unauthorized | No token, or it expired | `gh auth login`, then re-run `gh auth token`. For PAT: check it hasn't expired or been revoked. |
| **HTTP 403** Forbidden | Token is valid but lacks rights | PAT scope missing **Issues (Read & Write)** — reissue with that scope. For fine-grained PAT: confirm the repo is included in the token's access list. |
| **repo not found / 404** | Wrong owner/repo name, or private repo the token can't see | Check `GH_OWNER` / `GH_REPO` spelling. For private repos: confirm the token/PAT has repo access. |
| **"gh: command not found"** | gh CLI not installed | Install from https://cli.github.com, then `gh auth login`. Or fall back to Method B (`GH_TOKEN`). |
| **200 but wrong repo** | Env vars point at the wrong place | Re-check `GH_OWNER` / `GH_REPO` — exact casing, exact repo name. |

## Hand-off

Once `gh api repos/...` returns the full_name cleanly, auth is good — continue with
[[github-create-issues]] or [[findings-to-github-issues]]. Leave `GH_OWNER` / `GH_REPO`
set in the shell; they carry straight into all downstream skills.
```

Write to: `plugins/github-backlog/skills/github-auth/SKILL.md`

- [ ] **Step 2: Commit**

```bash
git add plugins/github-backlog/skills/github-auth/SKILL.md
git commit -m "feat(github-backlog): add github-auth skill"
```

---

## Task 7: extract-findings and triage-findings skills

These are the same logic as ado-backlog, updated to reference the github-backlog pipeline.

**Files:**
- Create: `plugins/github-backlog/skills/extract-findings/SKILL.md`
- Create: `plugins/github-backlog/skills/triage-findings/SKILL.md`

- [ ] **Step 1: Write extract-findings/SKILL.md**

```markdown
---
name: extract-findings
description: >-
  Normalize ANY input into findings.json — the first step toward turning review
  notes into a GitHub Issues backlog. Use whenever someone hands you a list of
  issues, discrepancies, gaps, review notes, or audit results they want to act
  on: an Excel/CSV/TSV audit sheet, a Word/PDF/Markdown spec, or chat/text pasted
  into the conversation. Trigger even when the user does NOT say "extract" — e.g.
  "here's a naming audit", "these are the problems we found", "turn this
  spreadsheet into GitHub issues", "I reviewed the code and noted these gaps",
  "make a backlog from this doc". If the goal is eventually GitHub Issues, this
  runs first. Hands off to triage-findings (then classify-github-issues,
  github-create-issues). Driven end-to-end by the findings-to-github-issues orchestrator.
---

# extract-findings

Turn whatever the user has — a spreadsheet, a doc, or pasted text — into a clean
`findings.json`. This is the entry point of the github-backlog pipeline: every later
step (triage, classify, create, write-back) keys off the fields you produce here,
so the value is a faithful, lossless normalization, not interpretation.

Output contract: `findings.json` shape in
`${CLAUDE_PLUGIN_ROOT}/references/data-contracts.md`. Read it before writing —
the field names are load-bearing and the bundled scripts depend on them.

## Schema (target)

Each finding normalizes to these fields (full table in data-contracts.md):

- `key` — **required.** Stable id per finding; carried through every later file so
  the created issue can be written back to the right source row.
- `current` / `expected` — **required.** Observed value vs the canonical/correct one.
- `section`, `recommendation`, `notes` — optional context; carried into the issue body.
- `kind` — optional: `rename | disambiguation | missing | other`. Helps the
  classifier pick labels.
- `severity` — optional: `Critical | High | Medium | Low`. Drives priority label + triage.
- `status` — optional free text (`confirmed`, `needs-review`, ...). A useful triage filter.

Top level also records `source` (a human-readable origin) and `keyColumn` (which
source column became `key`).

## 1. Get the content in front of you

**Spreadsheets** (`.xlsx`, `.xlsm`, `.csv`, `.tsv`) are binary or crash the Windows
cp1252 console, so don't open them blind — dump them to UTF-8 text first. The helper
forces UTF-8 so the rows survive intact:

```powershell
python "${CLAUDE_PLUGIN_ROOT}/scripts/read_source.py" "<path-to-file>"
```

Then read the printed dump. For a big sheet, write it to a file and Read that
(default cap is 200 rows; pass `--max-rows 0` for everything):

```powershell
python "${CLAUDE_PLUGIN_ROOT}/scripts/read_source.py" "<path-to-file>" --out "<workdir>/source-dump.txt" --max-rows 0
```

The dump prefixes each row with its index — `[0]` is usually the header row, `[1]`
onward the data. Multiple sheets are emitted under `=== SHEET: ... ===` markers.

**Non-tabular input** (`.docx`, `.pdf`, `.md`, `.txt`, or text pasted into the chat)
needs no helper — read it directly with the Read tool, or just use the pasted text.

## 2. Map source columns to schema fields

Look at the header row / structure and decide which column means `current`, which
means `expected`, etc. **When a column's meaning is unclear, ask the user rather
than guess silently.** A wrong mapping corrupts every downstream issue.

- `key`: prefer an existing stable column (a `#`, `ID`, or row-number column). If
  none exists, assign `"1","2","3",...` in row order. Record your choice in `keyColumn`.
- `kind` and `severity`: infer **only if the source actually supports it.**
- Keep `current`/`expected` verbatim — later steps put them in the issue body.

## 3. Write findings.json

Write it to a working directory **next to the source** so all pipeline artifacts
stay together. Tell the user the exact path you wrote.

## 4. Summarize and confirm before handoff

Show the user:
- the column → field mapping you used (and what `key` came from),
- counts: total findings, and a breakdown by `severity`/`kind` if you set them,
- the first 3–5 normalized findings.

Once the user confirms the mapping looks right, hand off to **triage-findings**.

## Notes

- `key` uniqueness matters — duplicate keys break write-back.
- Write-back to the source only works for spreadsheets.
- One finding per actionable discrepancy. Don't merge unrelated rows.
```

Write to: `plugins/github-backlog/skills/extract-findings/SKILL.md`

- [ ] **Step 2: Write triage-findings/SKILL.md**

```markdown
---
name: triage-findings
description: >-
  Decide WHICH findings become GitHub Issues and in what order/batches, working
  from a findings.json produced by extract-findings. Use this AFTER findings are
  extracted and BEFORE creating issues — especially when there are more findings
  than you want to file at once. Triggers on "start with the critical ones",
  "which should we file first", "don't dump everything into GitHub", "let's do
  this in batches/waves", "only the confirmed ones for now", "hold the
  needs-review items", "scope down the backlog", "prioritize these findings",
  or any request to pick a subset of findings to turn into issues. Produces a
  scoped, ordered subset and hands it to classify-github-issues.
---

# triage-findings

You have a `findings.json` (from `extract-findings`). Filing every row blindly
creates a noisy, unprioritized backlog. This skill is the human-in-the-loop gate:
**show the shape of the findings, agree on a scope and order, emit a smaller set**,
then hand off to `classify-github-issues`. The win is an auditable *wave* structure.

This is a reasoning/filtering step — there is no script to run. You read JSON,
summarize, and write a smaller JSON.

## 1. Read and profile the findings

Show counts before asking anything:

- **by `severity`**: Critical / High / Medium / Low (and how many have none)
- **by `status`**: `confirmed` vs `needs-review` (bucket what you see)
- **by `section`**: which areas the findings cluster in
- **by `kind`** (optional): `rename` / `disambiguation` / `missing` / `other`

```
42 findings total
  severity: Critical 6 | High 14 | Medium 18 | Low 4
  status:   confirmed 30 | needs-review 12
  section:  Cargo Classification 19 | Port Calls 11 | Misc 12
```

## 2. Recommend a default, then follow the user's call

**Recommended default: `severity = Critical` AND `status = confirmed` first.**
Hold `needs-review` for a later verification pass — filing unconfirmed findings
creates issues you may have to close.

Ask one focused question: *"Start with the 6 Critical + confirmed as wave 1, and
hold the 12 needs-review for a verification pass? Or a different cut?"*

## 3. Order within the scope

Order: **Critical → High → Medium → Low**, `confirmed` before softer statuses.
Stable-sort within a tie by `section`. This ordering carries into `github_backlog_input.json`.

## 4. Emit the scoped subset

Write `findings.wave1.json` (preferred for clean waves) or annotate findings in place
with `"selected": true`. Preserve every original field verbatim — especially `key`.

```json
{
  "source": "Downloads/CRM_Audit.xlsx",
  "keyColumn": "#",
  "findings": [
    { "key": "1", "severity": "Critical", "status": "confirmed", "kind": "rename",
      "current": "Auto", "expected": "Automotive Cargo" }
  ]
}
```

## 5. Hand off

Report the wave (count, filter applied, file written) and tell the user the next step:
**`classify-github-issues`** turns this scoped set into `github_backlog_input.json`.
Note any held-back waves so they are not forgotten.

## Notes

- Keep waves small enough to review before the next wave. 5–15 items is usually right.
- If `findings.json` has no `severity`/`status`, triage on `section`/`kind` or count, and say so.
- Triage writes nothing to GitHub — creation happens in `github-create-issues`.
```

Write to: `plugins/github-backlog/skills/triage-findings/SKILL.md`

- [ ] **Step 3: Commit**

```bash
git add plugins/github-backlog/skills/extract-findings/SKILL.md plugins/github-backlog/skills/triage-findings/SKILL.md
git commit -m "feat(github-backlog): add extract-findings and triage-findings skills"
```

---

## Task 8: classify-github-issues skill

**Files:**
- Create: `plugins/github-backlog/skills/classify-github-issues/SKILL.md`

- [ ] **Step 1: Write classify-github-issues/SKILL.md**

```markdown
---
name: classify-github-issues
description: >-
  Map triaged findings to GitHub Issues with the correct labels, milestone, and
  body, and emit github_backlog_input.json ready for creation. Use this AFTER
  triage and BEFORE creating issues — when the user asks "what labels should these
  get", "turn these findings into GitHub issues", "classify these for GitHub", or
  "build the github backlog input". Maps severity to priority labels (P0-P3),
  kind to type labels (bug/enhancement/task), and hours to size labels
  (size:XS-XL). Creates a milestone for the batch. Hands off to
  github-create-issues.
---

# classify-github-issues

Turn findings (from `extract-findings` + `triage-findings`) into a
`github_backlog_input.json` that `github-create-issues` can create. Unlike ADO,
GitHub Issues are flat — type, priority, and size are expressed as labels; the
batch grouping is a milestone; the parent tracker is a tracking issue created last.

Schemas live in `references/data-contracts.md` — read it for the exact shapes.

## 1. Map findings to label sets

For each finding, assign three labels:

**Type label** (pick one):

| finding kind | label |
|---|---|
| `rename` / `disambiguation` / wrong/mislabeled existing thing | `bug` |
| `missing` / net-new capability | `enhancement` |
| process / administrative work | `task` |
| docs-only change | `documentation` |

When a finding is ambiguous between `bug` and `enhancement`, ask the user.

**Priority label** (based on `severity`):

| severity | label |
|---|---|
| Critical | `P0` |
| High | `P1` |
| Medium | `P2` |
| Low | `P3` |
| (none) | `P2` — default Medium, note it |

**Size label** (based on estimated hours):

| hours | label |
|---|---|
| ≤ 2h | `size:XS` |
| 3–4h | `size:S` |
| 5–8h | `size:M` |
| 9–16h | `size:L` |
| > 16h | `size:XL` |

Use the same work-kind anchors as `classify-work-items` in ado-backlog:

| kind | baseline |
|---|---|
| rename (one spot) | 1–2h |
| rename (multi-screen) | 3–4h |
| disambiguation / mapping | 4–8h |
| missing field (UI + submit) | 6–8h |
| structural / new column | 4–6h |

If an item exceeds ~16h, propose splitting it instead.

## 2. Write the issue title

Specific and self-contained. Name the thing and the expected state:
- Good: `Portal label "Auto" should display "Automotive Cargo"`
- Bad: `Fix naming`

## 3. Write the issue body (Markdown)

```markdown
## Finding

**Current:** <current value>
**Expected:** <expected value>
**Section:** <section>

**Recommendation:** <recommendation>

<notes if any>

**Estimate:** Xh
```

The raw hour estimate goes at the bottom of the body as `**Estimate:** Xh` so it
survives label changes.

## 4. Propose a milestone

Name the batch milestone (e.g. `Audit Wave 1`, `Security Findings Q2 2026`). Ask
the user to confirm or rename it. `create_github_issues.py` creates the milestone
if it doesn't exist.

## 5. Decide assignees

A fresh backlog is usually created *unassigned* (assigned later in planning).
**Ask the user:** leave unassigned, assign to themselves, or map per-row. Use GitHub
username strings in `assignees[]`.

## 6. Show estimates table and get approval

Before writing the JSON, show a table and wait for explicit OK:

```
 key  | title (truncated)               | type        | priority | size   | est
------|---------------------------------|-------------|----------|--------|-----
 1    | Portal label "Auto" should...   | bug         | P1       | size:S | 4h
 2    | Add rate limiting to API        | enhancement | P2       | size:M | 6h
                                                                          ----
                                                                          ~10h
```

Let the user adjust any value before proceeding to the dry-run.

## 7. Write github_backlog_input.json

Assemble the full JSON per the contract in `references/data-contracts.md` and write
it next to the findings file. Every item must have a `key`, a non-empty `title`,
at least one label of each type/priority/size dimension, and a populated `body`.

Then hand off to **github-create-issues** for the visual dry-run and creation.
```

Write to: `plugins/github-backlog/skills/classify-github-issues/SKILL.md`

- [ ] **Step 2: Commit**

```bash
git add plugins/github-backlog/skills/classify-github-issues/SKILL.md
git commit -m "feat(github-backlog): add classify-github-issues skill"
```

---

## Task 9: github-create-issues skill

**Files:**
- Create: `plugins/github-backlog/skills/github-create-issues/SKILL.md`

- [ ] **Step 1: Write github-create-issues/SKILL.md**

```markdown
---
name: github-create-issues
description: >-
  Create GitHub Issues from a github_backlog_input.json (the output of
  classify-github-issues) via the bundled create_github_issues.py script. Always
  shows a visual dry-run table first and only creates real issues after the user
  explicitly approves. Use this whenever there is a github_backlog_input.json or
  any file of items to file in GitHub, or when the user says "create these GitHub
  issues", "file the backlog", "push these to GitHub", or "create the issues".
  This is the step that actually writes to the repo, so prefer it over hand-rolling
  API calls. After creating, it writes github_backlog_result.json for
  github-writeback-tracking.
---

# github-create-issues

Take a `github_backlog_input.json` and create the issues in GitHub by driving
the bundled `create_github_issues.py`. The script creates the milestone and labels
if needed, creates each issue, then creates a tracking issue with a task list
linking them all.

Creating issues is effectively un-undoable (close is manual; notifications already
fired). So this skill is built around a hard gate: **visual dry-run always, real
run only on an explicit "yes".**

For the exact JSON shapes see `${CLAUDE_PLUGIN_ROOT}/references/data-contracts.md`.

## Prerequisites

- **Auth** — `gh auth login` once (the script reads `gh auth token`). Or set
  `$env:GH_TOKEN`. See the `github-auth` skill.
- **Owner/repo** — set `$env:GH_OWNER` / `$env:GH_REPO`, or include `owner` /
  `repo` in the JSON. Env vars override the JSON.
- **Python + requests + openpyxl** — run the setup checker if unsure:
  `powershell -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check_github.ps1"`

## Step 1 — VISUAL DRY-RUN (creates nothing)

GitHub Issues has no `validateOnly` API. Instead: read `github_backlog_input.json`
and render a formatted table for the user to review before any API call.

Present:

```
 # | Key    | Title                              | Labels               | Assignee
---|--------|------------------------------------|----------------------|---------
 1 | row-1  | Portal label "Auto" should show... | bug, P1, size:S      | —
 2 | row-2  | Add rate limiting to API           | enhancement, P2, ... | pon
...
Milestone: Audit Wave 1
Tracking issue: yes (created last, links all above)
Total: 2 issues
```

> **GATE — stop here.** Do not proceed until the user has explicitly approved the
> list (e.g. "create them", "go ahead", "yes").

If the user requests changes, update `github_backlog_input.json` and re-render the
table. The table is free — re-rendering costs nothing.

## Step 2 — REAL RUN (only after explicit approval)

```powershell
$env:GH_OWNER = "Cartagena365"
$env:GH_REPO  = "GlassHull"
python "${CLAUDE_PLUGIN_ROOT}/scripts/create_github_issues.py" `
  --input  "<workdir>/github_backlog_input.json" `
  --output "<workdir>/github_backlog_result.json"
```

The script prints one line per created issue (`key X -> #N <url>`) and a final
`tracking issue -> #N <url>`. Then it writes `github_backlog_result.json`.

Relay the output to the user. Surface any failure clearly — a partial run is better
visible than silent.

## After creating — verify

Confirm the items landed. Check `github_backlog_result.json` — every item should
have a `number` and `url`. Items without a `number` failed; surface them to the user.

## Idempotency — don't double-create

`create_github_issues.py` is **not** idempotent: re-running on the same
`github_backlog_input.json` creates a second set of issues. After a successful run,
hand off to **github-writeback-tracking** to stamp `Issue #` / `Issue URL` back onto
source rows. Once a row carries an Issue #, treat it as done. To re-file a subset,
prune the input to only the un-filed `key`s first.
```

Write to: `plugins/github-backlog/skills/github-create-issues/SKILL.md`

- [ ] **Step 2: Commit**

```bash
git add plugins/github-backlog/skills/github-create-issues/SKILL.md
git commit -m "feat(github-backlog): add github-create-issues skill"
```

---

## Task 10: github-writeback-tracking and github-my-work skills

**Files:**
- Create: `plugins/github-backlog/skills/github-writeback-tracking/SKILL.md`
- Create: `plugins/github-backlog/skills/github-my-work/SKILL.md`

- [ ] **Step 1: Write github-writeback-tracking/SKILL.md**

```markdown
---
name: github-writeback-tracking
description: >-
  Add traceability columns to a spreadsheet source and write created GitHub issue
  numbers/URLs back into it, matched row-by-row by key. Use this right after
  creating issues — when you have a github_backlog_result.json and the original
  source was a spreadsheet (xlsx/csv). Triggers on "write the issue links back",
  "track which row got which issue", "update the spreadsheet with the GitHub IDs",
  "fill in the issue column", "close the loop on the audit sheet".
---

# github-writeback-tracking

Closes the loop: once issues exist in GitHub, stamp their numbers and URLs back onto
the spreadsheet the findings came from. The link between a row and its issue is the
**`key`** field, carried from [[extract-findings]] through `github_backlog_result.json`.

## When this applies

- **Spreadsheet sources only** (`.xlsx` / `.csv` / `.tsv`).
- **Doc / pasted-text sources**: skip the script; just report the created issue links from `github_backlog_result.json` in chat.
- You need `github_backlog_result.json` from [[github-create-issues]].

## Before you write

Back up the user's source file first — `github_tracking.py` edits it **in place**:

```powershell
Copy-Item "<file>.xlsx" "<file>.bak.xlsx"
```

## Step 1 — add tracking columns (idempotent)

Appends `Issue #`, `Issue URL`, `State`, `Created` after the last used column. Safe
to run repeatedly — columns that already exist are not duplicated.

```powershell
python "${CLAUDE_PLUGIN_ROOT}/scripts/github_tracking.py" add-columns --source "<file>" --key "#"
```

## Step 2 — write the issue links back (idempotent)

Matches each `github_backlog_result.json` item's `key` to the source key column and
fills the four tracking columns. Rows that already hold an `Issue #` are left as-is.

```powershell
python "${CLAUDE_PLUGIN_ROOT}/scripts/github_tracking.py" writeback `
  --source "<file>" `
  --result "<workdir>/github_backlog_result.json" `
  --key "#"
```

Per row it writes: `Issue #` ← `items[].number`, `Issue URL` ← `items[].url`,
`State` ← `open`, `Created` ← `YYYY-MM-DD HH:MM`.

## The `--key` must line up

The `--key` column name must match the `keyColumn` chosen in [[extract-findings]] and
the `key` values in `github_backlog_result.json`. Values are compared as strings.

If the script prints `warn: key <x> not found in source`, the key in the result
doesn't match any value in that column — re-check `--key` and that the source hasn't
been re-sorted since extraction.
```

Write to: `plugins/github-backlog/skills/github-writeback-tracking/SKILL.md`

- [ ] **Step 2: Write github-my-work/SKILL.md**

```markdown
---
name: github-my-work
description: >-
  Show open GitHub Issues assigned to you in the target repo, grouped by priority
  label (P0 first), with clickable issue links. Use whenever the user asks "what's
  on my plate", "my GitHub issues", "what should I work on next", "show my open
  issues", or starts the day wanting their remaining work. Read-only — it lists,
  it never changes anything.
---

# github-my-work

List open issues assigned to you in the target repo, sorted by priority (P0 → P1 →
P2 → P3 → unlabeled). Rendered as a table with clickable links. Entirely read-only.

## Run it

Prereqs: `gh auth login` (or `$env:GH_TOKEN`), `$env:GH_OWNER` + `$env:GH_REPO` set.

```powershell
$env:GH_OWNER = "Cartagena365"
$env:GH_REPO  = "GlassHull"
gh issue list `
  --repo "$env:GH_OWNER/$env:GH_REPO" `
  --assignee @me `
  --state open `
  --json number,title,labels,url `
  --jq '.[] | [.number, .title, (.labels | map(.name) | join(", ")), .url] | @tsv'
```

Format the output as a table sorted by priority label. Issues labeled `P0` come
first, then `P1`, `P2`, `P3`, then unlabeled. The `#` column should be a clickable
terminal hyperlink (use `\e]8;;URL\e\\TEXT\e]8;;\e\\` for OSC 8 links in terminals
that support them).

## After listing

The top P0/P1 item is the highest-priority actionable issue — a good "do next". If
the user wants to turn a *findings source* into new issues, hand off to
**findings-to-github-issues**.
```

Write to: `plugins/github-backlog/skills/github-my-work/SKILL.md`

- [ ] **Step 3: Commit**

```bash
git add plugins/github-backlog/skills/github-writeback-tracking/SKILL.md plugins/github-backlog/skills/github-my-work/SKILL.md
git commit -m "feat(github-backlog): add writeback-tracking and my-work skills"
```

---

## Task 11: findings-to-github-issues orchestrator

**Files:**
- Create: `plugins/github-backlog/skills/findings-to-github-issues/SKILL.md`

- [ ] **Step 1: Write findings-to-github-issues/SKILL.md**

```markdown
---
name: findings-to-github-issues
description: >-
  End-to-end orchestrator that turns findings from ANY input (audit spreadsheet,
  code/security review, QA report, meeting notes, a pasted list of issues) into
  a GitHub Issues backlog with a milestone, labels, and a tracking issue. Drives
  the sibling github-backlog skills in order with safety gates. Trigger whenever
  the user says "turn this audit/spreadsheet/review/list of issues into GitHub
  issues", "create a backlog from these findings", "file these as GitHub issues",
  "import this xlsx/csv into GitHub", "make issues from this report", or hands
  you a source document and asks for it to land in GitHub. This is the headline,
  one-shot entry point (/github-backlog:run wraps it). Not for editing existing
  issues individually.
---

# findings-to-github-issues (orchestrator)

Run the full pipeline: a source document in, a GitHub Issues backlog out. You
coordinate six sibling skills; each owns its step and its data contract. Your job
is to sequence them, keep the working files together, and enforce the safety gates
so nothing irreversible happens without the user seeing it first.

**Why an orchestrator:** the value is in the gates. Creating issues is a write the
user cannot easily undo (close is manual; notifications already fired), so the
pipeline is deliberately staged: read-only extraction and classification first, a
visual dry-run that creates nothing, an explicit human approval, then the real write.

## Data flow

```
extract-findings         -> findings.json
classify-github-issues   -> github_backlog_input.json  (consumed by create_github_issues.py)
github-create-issues     -> github_backlog_result.json (consumed by github_tracking.py)
```

**Working directory:** create one beside the source and keep all JSON files there.

## Process

### 0. Prereqs + auth (recommended on first run)

```powershell
powershell -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check_github.ps1"
```

Checks gh CLI, Python + requests + openpyxl, `GH_OWNER` / `GH_REPO`, and repo
reachability. For auth specifics, delegate to **github-auth**.

### 1. Extract → `findings.json` (delegate to **extract-findings**)

Have **extract-findings** read the source and normalize it to `findings.json`.
**Confirm the column mapping with the user** before moving on — which column is the
`key`, which are `current` / `expected`, where `severity` and `status` come from.

### 2. Triage → scoped subset (delegate to **triage-findings**)

Have **triage-findings** filter `findings.json` to the wave worth creating now.
**Recommend Critical + confirmed first.** Hold `needs-review` for a later wave.

### 3. Classify → `github_backlog_input.json` (delegate to **classify-github-issues**)

Have **classify-github-issues** map the scoped findings to GitHub Issues with labels,
milestone, body, and size estimate. It will show an estimates table.

> **GATE — estimates.** Show the table and get the user's OK / adjustments before
> the visual dry-run.

### 4. VISUAL DRY-RUN → validate, create nothing (delegate to **github-create-issues**)

Have **github-create-issues** render `github_backlog_input.json` as a formatted
table — title, labels, milestone, assignee per item. Nothing is created.

> **GATE — stop here.** Do not proceed until the user has explicitly approved the
> list. Present the count, the milestone, and the labels, and wait for a clear yes.

### 5. REAL RUN → `github_backlog_result.json` (delegate to **github-create-issues**)

Only after approval. The script creates labels, the milestone, each issue, then the
tracking issue:

```powershell
$env:GH_OWNER = "Cartagena365"
$env:GH_REPO  = "GlassHull"
python "${CLAUDE_PLUGIN_ROOT}/scripts/create_github_issues.py" `
  --input  "<workdir>/github_backlog_input.json" `
  --output "<workdir>/github_backlog_result.json"
```

Then **verify the created items** — confirm each `key` got a `number` and `url` in
`github_backlog_result.json`, and surface any that failed.

### 6. Write-back tracking — spreadsheets only (delegate to **github-writeback-tracking**)

**Only if the source is a spreadsheet.**

> **GATE — back up the source first.**

Have **github-writeback-tracking** drive `github_tracking.py`: first `add-columns`,
then `writeback`. Both subcommands are idempotent.

### 7. Report back

Summarize the run:
- **Created:** count + clickable links + tracking issue link.
- **Held / skipped:** the triage wave deferred, plus any real-run errors.
- **Follow-ups:** the obvious next wave.

## Safety gates (non-negotiable)

1. **Visual dry-run before real run** — step 4 always precedes step 5.
2. **Explicit approval before any write** — never jump from classification to creation.
3. **Back up the source before write-back** — step 6 edits the file in place.
```

Write to: `plugins/github-backlog/skills/findings-to-github-issues/SKILL.md`

- [ ] **Step 2: Commit**

```bash
git add plugins/github-backlog/skills/findings-to-github-issues/SKILL.md
git commit -m "feat(github-backlog): add findings-to-github-issues orchestrator"
```

---

## Task 12: Commands

**Files:**
- Create: `plugins/github-backlog/commands/run.md`
- Create: `plugins/github-backlog/commands/my-work.md`
- Create: `plugins/github-backlog/commands/setup-check.md`
- Create: `plugins/github-backlog/commands/github-auth.md`

- [ ] **Step 1: Write run.md**

```markdown
---
description: Run the full findings -> GitHub Issues process on a file or pasted text. Extract findings, triage, classify by labels and milestone, visual dry-run, then create on approval and write issue links back. Use whenever someone wants to turn an audit/spreadsheet/list of issues into GitHub Issues.
argument-hint: "[path-to-findings-file]"
---

Use the **`findings-to-github-issues`** skill to turn the input below into a GitHub Issues backlog.

Input: $ARGUMENTS

Follow the skill end to end, and **stop at the visual dry-run gate** — show me exactly what will be
created and wait for my explicit approval before creating anything in GitHub.
```

Write to: `plugins/github-backlog/commands/run.md`

- [ ] **Step 2: Write my-work.md**

```markdown
---
description: List open GitHub Issues assigned to you in the target repo, grouped by priority label. The daily "what's on my plate" view for GitHub-based work.
argument-hint: ""
---

Use the **`github-my-work`** skill to list my assigned open issues.

$ARGUMENTS
```

Write to: `plugins/github-backlog/commands/my-work.md`

- [ ] **Step 3: Write setup-check.md**

```markdown
---
description: Verify all prerequisites for the github-backlog pipeline — gh CLI, Python, requests, openpyxl, GH_OWNER/GH_REPO env vars, and repo reachability. Read-only.
argument-hint: ""
---

Use the **`github-auth`** skill to run the setup checker:

```powershell
powershell -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check_github.ps1"
```

Report any FAIL lines with their fix. WARN lines (missing env vars) are OK before the pipeline starts.
```

Write to: `plugins/github-backlog/commands/setup-check.md`

- [ ] **Step 4: Write github-auth.md**

```markdown
---
description: Authenticate to GitHub and diagnose auth failures. Covers gh CLI and GH_TOKEN methods, verify snippet, and 401/403 troubleshooting.
argument-hint: ""
---

Use the **`github-auth`** skill to verify GitHub authentication.

$ARGUMENTS
```

Write to: `plugins/github-backlog/commands/github-auth.md`

- [ ] **Step 5: Commit**

```bash
git add plugins/github-backlog/commands/
git commit -m "feat(github-backlog): add commands (run, my-work, setup-check, github-auth)"
```

---

## Task 13: README and QUICKSTART

**Files:**
- Create: `plugins/github-backlog/README.md`
- Create: `plugins/github-backlog/QUICKSTART.md`

- [ ] **Step 1: Write README.md**

```markdown
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
```

Write to: `plugins/github-backlog/README.md`

- [ ] **Step 2: Write QUICKSTART.md**

```markdown
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
```

Write to: `plugins/github-backlog/QUICKSTART.md`

- [ ] **Step 3: Commit**

```bash
git add plugins/github-backlog/README.md plugins/github-backlog/QUICKSTART.md
git commit -m "feat(github-backlog): add README and QUICKSTART"
```

---

## Self-review

**Spec coverage check:**

| Spec requirement | Covered by |
|---|---|
| Separate `github-backlog` plugin, same marketplace | Task 1 |
| `gh` CLI primary, `GH_TOKEN` fallback | Task 4 (`create_github_issues.py`), Task 6 (`github-auth` skill) |
| GitHub Issues only (no Projects) | Not implementing Projects — confirmed non-goal |
| Visual dry-run + explicit approval | Task 9 (`github-create-issues` skill) |
| Python create script | Task 4 |
| Flat label style: `bug`/`enhancement`/`task`, `P0`-`P3`, `size:XS`-`size:XL` | Tasks 4, 8 |
| Auto-create missing labels | Task 4 (`ensure_labels`) |
| Milestone as batch grouping | Tasks 4, 8 |
| Tracking issue with task list | Task 4 (`create_tracking_issue`) |
| `github_backlog_input.json` / `github_backlog_result.json` schemas | Task 2 |
| `findings.json` identical to ado-backlog | Task 7 (extract-findings references same schema) |
| `github_tracking.py` write-back | Task 5 |
| `setup_check_github.ps1` | Task 3 |
| `github-my-work` skill | Task 10 |
| `findings-to-github-issues` orchestrator + safety gates | Task 11 |
| 4 commands | Task 12 |
| QUICKSTART.md step-by-step | Task 13 |
| marketplace.json registration | Task 1 |
| CONTEXT.md terms | Already done in grilling session |
