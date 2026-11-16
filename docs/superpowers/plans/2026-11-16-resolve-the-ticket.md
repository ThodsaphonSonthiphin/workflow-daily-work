# resolve-the-ticket Implementation Plan

> **Superseded in part (2026-11-16, during execution).** Task 1's reference template says a
> child is done only at State category Resolved or Completed; ADR 0330 adds the State named
> Resolved, because the measured Agile process files Resolved under InProgress. Task 1's
> GitHub reads are `gh issue view … --json number,title,state,body,comments` and
> `gh api --paginate …/sub_issues`, with `@tsv` jq filters (Windows PowerShell 5.1). The
> committed `plugins/dev-workflows/skills/resolve-the-ticket/references/ticket-family.md`
> is authoritative over the template in Task 1 Step 5.
> ADRs renumbered 2026-11-16 from 0293-0307 to 0316-0330 (old + 23): origin/main had minted 0290-0315 for cut-vlog. Commit subjects before the renumber keep the old numbers.
> The committed SKILL.md, evals.json and ticket-family.md are authoritative over Task 2's text: the final review added a Removed carve-out, the split-table-only rule (ADR 0332), measured over cited, additions differ, the GitHub closing line, the record step on NOT READY, eval 7, requirement-text staleness (ADR 0331) and the file-only hand-off (ADR 0333).

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `resolve-the-ticket` skill in the `dev-workflows` plugin: a briefing before work starts and a read-only check before a person sets a ticket to Resolved.

**Architecture:** A prose skill (no script). One `SKILL.md` carries the flow; one reference file carries the measured tracker commands for the parent / child read; an `evals.json` carries seven cases. The skill loads `ticket-trace`, `read-picture` and `guide-and-verify`, and borrows `why-this-logic`'s splitting rules and proof-mark words.

**Tech Stack:** Markdown, YAML frontmatter, JSON; PowerShell + `az` and `gh` for the measured commands; Python 3.10+ for `scripts/generate_skills_tree.py` and `scripts/check_skills_tree.py`.

**Spec:** `docs/superpowers/specs/2026-11-16-resolve-the-ticket-design.md` (approved 2026-11-16). Decisions: `docs/adr/workflow-daily-work-0316-…` to `…-0329-…`. Glossary: `CONTEXT.md`, section *resolve-the-ticket terms*.

## Global Constraints

- The skill never writes to a tracker: no comment, no State change, no ticked box (ADR 0318).
- The skill builds nothing, fixes nothing, never authors a runbook, never invokes a skill it names for a gap (ADRs 0316, 0326, 0327).
- Its only write is a dated `## Resolve check` block appended to the ticket's runbook; it never edits a line above that block (ADR 0325).
- Trackers: Azure DevOps and GitHub Issues only; any other URL stops the run (ADR 0328).
- Skill name `resolve-the-ticket`; command `/dev-workflows:resolve-the-ticket`; plugin `dev-workflows` (ADR 0329).
- Harness-neutral wording: say "load the skill through your harness's mechanism", never name one harness's tool. `${CLAUDE_PLUGIN_ROOT}` only in the shapes `/references/…`, `/scripts/…`, `/skills/…`; the skill's own files use skill-relative paths (`references/ticket-family.md`).
- Version: `dev-workflows` `0.62.0` -> `0.63.0` in BOTH `plugins/dev-workflows/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Re-check the global max across every ref immediately before the version commit; if another ref already holds `0.63.0` or higher, take that max + 1.
- `skills/` is generated: never hand-edit it; run `python scripts/generate_skills_tree.py`.
- The working tree holds another session's uncommitted work: `plugins/dev-workflows/skills/guide-and-verify/SKILL.md`, `skills/guide-and-verify/SKILL.md`, `docs/adr/workflow-daily-work-0290-…md`, `docs/adr/workflow-daily-work-0291-…md`, `docs/reflections/2026-11.md`. Never edit, stage or commit these. Every `git add` in this plan names its files; never use `git add -A` or `git add .`.
- Work on branch `feat/resolve-the-ticket`, not on `main`. Commit only as the steps say.
- Commit messages end with the line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Windows + PowerShell. Write files as UTF-8 without BOM. Use `-` (hyphen), not an em dash, in the new `resolve-the-ticket` files. Rows added to `PLAYBOOK.md` and `daily/SKILL.md` follow those files' existing punctuation.

## File Structure

| File | Responsibility |
|---|---|
| `plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md` | the whole flow: opening, read, find files, briefing, check, verdict, record |
| `plugins/dev-workflows/skills/resolve-the-ticket/references/ticket-family.md` | measured commands for parent, children, links and done State on both trackers |
| `plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json` | seven eval cases |
| `plugins/dev-workflows/commands/resolve-the-ticket.md` | thin command wrapper |
| `PLAYBOOK.md`, `plugins/dev-workflows/skills/daily/SKILL.md` | discoverability |
| both manifests | version and description |
| `skills/resolve-the-ticket/`, `skills/daily/` | generated copies |

---

### Task 0: Branch and commit the design record

**Files:**
- Commit (already on disk): `docs/adr/workflow-daily-work-0316-…md` to `…-0329-…md` (14 files), `docs/superpowers/specs/2026-11-16-resolve-the-ticket-design.md`, `docs/superpowers/plans/2026-11-16-resolve-the-ticket.md`, `CONTEXT.md`

**Interfaces:**
- Produces: branch `feat/resolve-the-ticket` with the design record committed.

- [ ] **Step 1: Create the branch**

```powershell
git switch -c feat/resolve-the-ticket
```

- [ ] **Step 2: Confirm the ADR numbers are still free on every ref**

```powershell
git for-each-ref --format='%(refname:short)' refs/heads refs/remotes | ForEach-Object { git ls-tree -r --name-only --full-tree $_ -- docs/adr } | Select-String -Pattern '-(031[6-9]|032[0-9]|033[0-3])-' | Sort-Object -Unique
```

Expected: no output (no other ref holds 0316-0329). If a line prints, stop and report the clash - do not renumber on your own.

- [ ] **Step 3: Stage exactly the design files and commit**

```powershell
git add CONTEXT.md docs/superpowers/specs/2026-11-16-resolve-the-ticket-design.md docs/superpowers/plans/2026-11-16-resolve-the-ticket.md
Get-ChildItem docs/adr -Name | Where-Object { $_ -match '^workflow-daily-work-(031[6-9]|032[0-9]|033[0-3])-' } | ForEach-Object { git add "docs/adr/$_" }
git status --short
```

Expected: 17 files staged (`A` or `M` in the first column); the five files of the other session still show ` M` / `??` and are NOT staged.

```powershell
git commit -m "docs(resolve-the-ticket): ADRs 0316-0329, spec and plan - a briefing before the work and a read-only check before the resolve" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 1: Measure the ticket-family commands and write the reference

**Files:**
- Create: `plugins/dev-workflows/skills/resolve-the-ticket/references/ticket-family.md`

**Interfaces:**
- Consumes: `plugins/dev-workflows/skills/ticket-trace/references/ado.md` (token, single work item, comments, attachments - do not repeat them).
- Produces: `references/ticket-family.md` with four headed sections the SKILL.md points at by name: `## Azure DevOps - parent, children, links`, `## Azure DevOps - which States are done`, `## GitHub Issues - parent, children, links`, `## GitHub Issues - done State`.

Every command below is READ-ONLY (`GET`). Run each one once against a real ticket and record what came back. Azure DevOps: org `MackayGoodwin`, project `Elevate`, work item `151` (known: parent 147, child 297). GitHub: pick an issue with sub-issues - list candidates with `gh issue list --repo ThodsaphonSonthiphin/workflow-daily-work --label decision-map:map --state all --limit 5`. If a tracker cannot be reached (not logged in, 401/403, no issue with sub-issues), do not guess: keep the command in the file and write `Not measured: <reason>, <date>` under it, then report that in your task summary.

- [ ] **Step 1: Measure the Azure DevOps relations read**

```powershell
$token = az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv
$h = @{ Authorization = "Bearer $token" }
$r = Invoke-RestMethod -Headers $h -Uri ('https://dev.azure.com/MackayGoodwin/Elevate/_apis/wit/workitems/151?$expand=relations&api-version=7.0')
$r.rev
$r.relations | ForEach-Object { '{0}  {1}  {2}' -f $_.rel, ($_.url -replace '.*/',''), $_.attributes.name }
```

Expected: one line per link. `System.LinkTypes.Hierarchy-Reverse … Parent` names the parent's id; `System.LinkTypes.Hierarchy-Forward … Child` names each child; other `rel` values are the remaining links (`System.LinkTypes.Related`, `System.LinkTypes.Dependency-Reverse` = Predecessor, `System.LinkTypes.Dependency-Forward` = Successor; `ArtifactLink` / `AttachedFile` are not tickets). Record the exact `rel` strings and `attributes.name` values that came back.

- [ ] **Step 2: Measure the title-and-State batch read for linked tickets**

Replace the ids with the non-parent, non-child ids from Step 1.

```powershell
$ids = '272,145,295'
(Invoke-RestMethod -Headers $h -Uri ("https://dev.azure.com/MackayGoodwin/Elevate/_apis/wit/workitems?ids=$ids&fields=System.Id,System.WorkItemType,System.Title,System.State&api-version=7.0")).value | ForEach-Object { '#{0}  {1}  {2}  {3}' -f $_.id, $_.fields.'System.WorkItemType', $_.fields.'System.State', $_.fields.'System.Title' }
```

Expected: one line per id with type, State and title.

- [ ] **Step 3: Measure the done-State read**

```powershell
(Invoke-RestMethod -Headers $h -Uri 'https://dev.azure.com/MackayGoodwin/Elevate/_apis/wit/workitemtypes/User%20Story/states?api-version=7.0').value | ForEach-Object { '{0}  ->  {1}' -f $_.name, $_.category }
```

Expected: each State name with a category out of `Proposed`, `InProgress`, `Resolved`, `Completed`, `Removed`. Record the pairs that came back.

- [ ] **Step 4: Measure the GitHub reads**

Set `$repo` and `$n` to the issue picked above.

```powershell
$repo = 'ThodsaphonSonthiphin/workflow-daily-work'; $n = 0   # put the issue number here
gh issue view $n --repo $repo --json number,title,state,body,comments --jq '{number,title,state}'
gh api "repos/$repo/issues/$n/sub_issues" --jq '.[] | "#\(.number)  \(.state)  \(.title)"'
gh api "repos/$repo/issues/$n/parent" --jq '"#\(.number)  \(.state)  \(.title)"'
```

Expected: the first prints the issue; the second prints one line per sub-issue; the third prints the parent, or returns HTTP 404 when the issue has none. Run the third again on one of the sub-issues to see a parent that exists. Record which of the three answered and what an absent parent looks like.

- [ ] **Step 5: Write `references/ticket-family.md`**

Write the file with this content, then replace each `Measured:` line with what you saw in Steps 1-4 (the date, the ticket, and the exact strings), and correct any command or field name that did not behave as written. A command you could not run keeps its `Not measured:` line.

````markdown
# Ticket family - parent, children, links, done State

Read-only commands for the part of a ticket read that `ticket-trace` does not carry. The
token, one work item's fields, its comments and its attached images are in
`${CLAUDE_PLUGIN_ROOT}/skills/ticket-trace/references/ado.md` - use those as written.

Take `{org}`, `{project}` and `{id}` (or `{owner}`, `{repo}`, `{n}`) from the ticket URL the
user gave. Never take them from an environment variable or from another ticket.

## Azure DevOps - parent, children, links

```powershell
$r = Invoke-RestMethod -Headers @{Authorization="Bearer $token"} -Uri ('https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{id}?$expand=relations&api-version=7.0')
$r.rev
$r.relations | ForEach-Object { '{0}  {1}  {2}' -f $_.rel, ($_.url -replace '.*/',''), $_.attributes.name }
```

| `rel` | meaning | read |
|---|---|---|
| `System.LinkTypes.Hierarchy-Reverse` | the parent | in full |
| `System.LinkTypes.Hierarchy-Forward` | a child | in full |
| `System.LinkTypes.Related` | related | type, title, State |
| `System.LinkTypes.Dependency-Reverse` | predecessor | type, title, State |
| `System.LinkTypes.Dependency-Forward` | successor | type, title, State |
| `ArtifactLink`, `AttachedFile`, `Hyperlink` | not a ticket | skip |

The id is the last segment of the relation's `url`. Keep `$r.rev`: the check block records
it, and a later run re-splits the rows when it has changed.

Title and State of the linked tickets, in one call:

```powershell
(Invoke-RestMethod -Headers @{Authorization="Bearer $token"} -Uri 'https://dev.azure.com/{org}/{project}/_apis/wit/workitems?ids={id1},{id2}&fields=System.Id,System.WorkItemType,System.Title,System.State&api-version=7.0').value
```

Measured: <date>, <org>/<project> #<id> - <what came back>

## Azure DevOps - which States are done

A State name differs by process (Resolved, Closed, Done). Read the category, not the name:

```powershell
(Invoke-RestMethod -Headers @{Authorization="Bearer $token"} -Uri 'https://dev.azure.com/{org}/{project}/_apis/wit/workitemtypes/{type}/states?api-version=7.0').value | ForEach-Object { '{0}  ->  {1}' -f $_.name, $_.category }
```

URL-encode a type with a space (`User%20Story`). A child is **done** when its State's
category is `Resolved` or `Completed`. `Removed` is not done and not open: show it as
`removed` and leave it out of the verdict.

Measured: <date>, <org>/<project>, type <type> - <the name -> category pairs>

## GitHub Issues - parent, children, links

```powershell
gh issue view {n} --repo {owner}/{repo} --comments
gh api "repos/{owner}/{repo}/issues/{n}/sub_issues" --jq '.[] | "#\(.number)  \(.state)  \(.title)"'
gh api "repos/{owner}/{repo}/issues/{n}/parent" --jq '"#\(.number)  \(.state)  \(.title)"'
```

The parent call answers HTTP 404 when the issue has no parent - that is "no parent", not a
failure. Other links are the `#<number>` mentions in the body and the comments: read each
with `gh issue view <number> --repo {owner}/{repo} --json number,title,state`.

Acceptance Criteria on GitHub are a task list (`- [ ] …`) or the lines under a heading
that reads "Acceptance criteria" in the body. Neither found: say "no AC section in the
issue" - never invent the lines from the title.

Measured: <date>, <owner>/<repo> #<n> - <what came back>

## GitHub Issues - done State

`state` is `open` or `closed`. A child is **done** when it is `closed`.

Measured: <date>, <owner>/<repo> #<n> - <what came back>

## Gotchas

- 401 / 403 on Azure DevOps: the token is expired or from the wrong account - `az login`
  with the work account, then read the token again.
- 404 on a work item: the number is in another project. Check the URL; do not try other
  projects.
- A relation whose `url` contains `/_apis/wit/attachments/` or starts `vstfs:` is a file or
  a commit, not a ticket.
````

- [ ] **Step 6: Verify the file**

```powershell
$f = 'plugins/dev-workflows/skills/resolve-the-ticket/references/ticket-family.md'
(Select-String -Path $f -Pattern '^## ').Line
Select-String -Path $f -Pattern '<date>|<what came back>|<the name' | Measure-Object | Select-Object -ExpandProperty Count
```

Expected: the five headings (`## Azure DevOps - parent, children, links`, `## Azure DevOps - which States are done`, `## GitHub Issues - parent, children, links`, `## GitHub Issues - done State`, `## Gotchas`), then `0` - no template marker left; each `Measured:` line holds real values or reads `Not measured: <reason>, <date>`.

- [ ] **Step 7: Commit**

```powershell
git add plugins/dev-workflows/skills/resolve-the-ticket/references/ticket-family.md
git commit -m "feat(resolve-the-ticket): the ticket-family reference - parent, children, links and done State, measured on both trackers (ADRs 0322, 0328)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: The eval cases, the skill and the command

**Files:**
- Create: `plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json`
- Create: `plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md`
- Create: `plugins/dev-workflows/commands/resolve-the-ticket.md`

**Interfaces:**
- Consumes: `references/ticket-family.md` and its four section headings (Task 1).
- Produces: skill name `resolve-the-ticket`; the seven result words `pass`, `pass - differs by decision`, `no test`, `fail`, `stale`, `differs`, `open`; the verdict lines `READY TO RESOLVE: YES` / `READY TO RESOLVE: NO`; the record heading `## Resolve check - <date> <time UTC> - READY | NOT READY`. Task 3 quotes the skill name only.

The evals are this skill's tests: write them first, confirm they parse, then write the SKILL.md that satisfies them.

- [ ] **Step 1: Write `evals/evals.json`**

```json
{
  "skill_name": "resolve-the-ticket",
  "evals": [
    {
      "id": 0,
      "name": "check-not-ready-no-test-and-open-child",
      "prompt": "resolve the ticket - check - https://dev.azure.com/Contoso/Ops/_workitems/edit/151 . You cannot reach the board from here, so here is what it holds. #151 User Story, State Active, rev 8, parent #147 Feature (New), child #297 Task (New, 'Add the case code to the reminder subject'). Acceptance Criteria: 'Runs Mon-Fri 08:00 AEST.' Description logic: 'filter: loggingstatus eq 914120001 or loggingstatus eq 914120003'. The runbook is documents/runbook-ado-151-overduereport-flow.md and its Outcome log has one line: 'S3c passed 2026-11-09 06:58Z - trigger fires Mon-Fri 08:00 AEST'. Nothing in the repo changed after 2026-11-09. If you ask whether the filter was tested: no. If you ask about #297: it is not done.",
      "expected_output": "A check table with four rows, the verdict READY TO RESOLVE: NO, one gap line per kind naming the next skill, no closing comment, and a Resolve check block for the runbook.",
      "files": [],
      "assertions": [
        "The table has four rows: one for the AC line, two for the filter (the or term, and the codes 914120001 / 914120003 together, per why-this-logic's splitting rules) and one for child #297",
        "The AC row is a pass marked cited, with the runbook as its locator and the date 2026-11-09",
        "Both filter rows' result is no test",
        "The #297 row is open and keeps the ticket not ready",
        "The verdict line reads READY TO RESOLVE: NO",
        "One gap line names generating-test-cases for both filter rows",
        "A gap line names resolve-the-ticket on #297 for the open child",
        "No closing comment is drafted",
        "Nothing is written or offered to be written to Azure DevOps - no comment post, no State change",
        "The skill does not check #297's own acceptance criteria in this run",
        "A '## Resolve check' block dated in UTC is appended to the runbook, after its last section"
      ]
    },
    {
      "id": 1,
      "name": "check-ready-with-a-told-row",
      "prompt": "resolve the ticket, check, https://github.com/acme/billing/issues/42 . The issue (open) has no parent and no sub-issues. Its body has: '## Acceptance criteria\\n- [ ] Invoices over 10,000 need a second approver\\n- [ ] The approver gets an email'. tests/approval.test.ts:14 asserts the 10,000 threshold and the suite passes when you run it (assume `npm test` printed 12 passed, 0 failed just now). There is no test for the email. When you ask me: I tested the email by hand today, it arrived. The runbook is docs/runbook-42-approval.md. No commit touched src/approval.ts after the test file's last change.",
      "expected_output": "Two rows, both pass - one measured, one told - the verdict READY with the count of rows resting on the user's word, a drafted closing comment carrying the told mark, and the State left to the person.",
      "files": [],
      "assertions": [
        "The threshold row is a pass marked measured, citing the test run of this session",
        "The email row is a pass marked told, with who and the date",
        "The verdict reads READY TO RESOLVE: YES and says one row rests on the user's word",
        "A closing comment is drafted as raw Markdown in one code block",
        "The drafted comment shows the told mark on the email row",
        "The skill tells the person to paste the comment and close the issue themselves",
        "The skill does not close the issue, post the comment or tick the task list",
        "A '## Resolve check' block is appended to docs/runbook-42-approval.md"
      ]
    },
    {
      "id": 2,
      "name": "stale-pass",
      "prompt": "check before resolve: https://dev.azure.com/Contoso/Ops/_workitems/edit/88 . #88 Bug, Active, rev 5, parent #80, no children. Acceptance Criteria: 'The export keeps leading zeros in the account number.' The runbook documents/runbook-ado-88-export.md says 'T2 passed 2026-11-10 02:01Z - account 00123 exported as 00123'. `git log -1 --format=%cI -- src/export.cs` gives 2026-11-12T09:30:00+00:00 (commit 'fix 88: also trim spaces').",
      "expected_output": "One row shown as STALE with both dates, verdict NOT READY, and a gap line that names the test step to run again.",
      "files": [],
      "assertions": [
        "The row's result is stale, not pass",
        "The row shows both dates: the pass on 2026-11-10 and the change on 2026-11-12",
        "The verdict line reads READY TO RESOLVE: NO",
        "The gap line names test step T2 as the step to run again",
        "The skill says the row can also be closed by the user stating the change does not touch it, marked told",
        "No closing comment is drafted"
      ]
    },
    {
      "id": 3,
      "name": "differs-by-decision-and-differs-without",
      "prompt": "resolve the ticket check https://dev.azure.com/Contoso/Ops/_workitems/edit/151 . #151 User Story, Active, rev 8, parent #147, no children. The description has two rules: (a) 'cut-off = startOfDay(addDays(utcNow(), -7))' and (b) 'send the reminder to CaseStaffEmail'. The runbook documents/runbook-ado-151.md says: 'D2 - approved by Pon 2026-11-09: the cut-off uses the Melbourne date, following Tech Spec p15 section 10.1, not the UTC day' and 'S3c passed 2026-11-09 07:06Z - cut-off computed from the Melbourne date' and 'S4c passed 2026-11-09 08:13Z - reminder sent to CaseStaffEmail with the admin in CC'. No decision in the runbook, the ticket comments or docs/adr mentions the CC. Nothing changed after 2026-11-09.",
      "expected_output": "Rule (a) passes as 'differs by decision D2'; rule (b) is DIFFERS with no written decision; verdict NOT READY; the gap line names grill-then-plan.",
      "files": [],
      "assertions": [
        "Rule (a) reads pass - differs by decision D2, with the runbook as the decision's locator",
        "Rule (b) reads differs, because the build adds a CC the ticket does not state and no written decision covers it",
        "The verdict line reads READY TO RESOLVE: NO",
        "The gap line for rule (b) names grill-then-plan",
        "The skill does not treat the passing test S4c as enough for rule (b)",
        "The skill does not edit the ticket or propose to edit it itself"
      ]
    },
    {
      "id": 4,
      "name": "briefing-before-the-work",
      "prompt": "brief me on this ticket before I start: https://dev.azure.com/Contoso/Ops/_workitems/edit/155 . #155 User Story, New, rev 3, parent #152 Feature (New), no children, related #153 (Active). Acceptance Criteria: 'The agent answers only from the approved FAQ.' and 'The agent never predicts a dividend.' The repo has documents/runbook-ado-155-faq.md (baseline only, no steps yet) and docs/why/155-faq-source.md.",
      "expected_output": "A briefing in chat: the ticket line, the family table, both AC lines quoted with locators, the file list with which to open first, open points. No check table, no verdict, no file written.",
      "files": [],
      "assertions": [
        "States the ticket's type, title or id, State and revision in one line",
        "Shows a family table with parent #152 and the related #153 with its State",
        "Quotes both AC lines as written, each with a locator such as #155 AC-1",
        "Lists the runbook and the why file, and says which to open first",
        "Points out that the related ticket #153 is still open",
        "Prints no check table and no READY verdict",
        "Writes no file and appends nothing to the runbook",
        "Builds nothing and proposes no implementation"
      ]
    },
    {
      "id": 5,
      "name": "no-runbook-hands-off",
      "prompt": "resolve the ticket, check, https://dev.azure.com/Contoso/Ops/_workitems/edit/297 . #297 Task, Active, rev 2, parent #151, no children. Acceptance Criteria: 'The reminder subject contains the case code.' You searched the project for 297: no file name and no file content carries it, and no commit message does.",
      "expected_output": "States that no runbook was found for #297 and hands off to guide-and-verify to create it; does not write a runbook itself and does not continue as if the check were complete.",
      "files": [],
      "assertions": [
        "Says plainly that no runbook was found for #297",
        "Names guide-and-verify as the skill that creates the runbook and hands off to it",
        "Passes what it already read (the ticket, its parent, the search result) as the head start",
        "Does not author a runbook file itself",
        "Does not use the parent's runbook as the place for the check",
        "Does not print READY TO RESOLVE: YES"
      ]
    },
    {
      "id": 6,
      "name": "opening-asks-and-refuses-unknown-tracker",
      "prompt": "resolve the ticket 151",
      "expected_output": "One question asking for the moment (briefing or check) and the ticket URL; nothing is read first. A follow-up with a Jira URL gets a plain refusal.",
      "files": [],
      "assertions": [
        "Asks, in one question, whether this is the briefing or the check and for the ticket's URL",
        "Does not guess the organization or project from the bare number or from an environment variable",
        "Reads no ticket and searches no file before the URL is given",
        "Given https://acme.atlassian.net/browse/OPS-151 as the answer, says it cannot read that tracker and stops"
      ]
    }
  ]
}
```

- [ ] **Step 2: Confirm the evals file parses and has eight cases**

```powershell
python -c "import json; d=json.load(open('plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json', encoding='utf-8')); print(d['skill_name'], len(d['evals']), [e['id'] for e in d['evals']])"
```

Expected: `resolve-the-ticket 8 [0, 1, 2, 3, 4, 5, 6, 7]`

- [ ] **Step 3: Confirm the skill does not exist yet (the failing state)**

```powershell
Test-Path plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md
```

Expected: `False`

- [ ] **Step 4: Write `SKILL.md`**

````markdown
---
name: resolve-the-ticket
description: 'Read-only helper for one ticket at two moments. BRIEFING before the work starts - what the ticket asks, its parent and children, linked tickets, the runbook and the files to open. CHECK before a person sets it to Resolved - one row per Acceptance Criteria line, logic rule and child ticket, each with its test and result (pass cited / measured / told, no test, fail, stale, differs, open), then READY or NOT READY and, on READY, a closing comment to paste. Asks which moment and waits for the ticket URL (Azure DevOps or GitHub Issues). Use for "resolve the ticket", "is this ticket ready to resolve", "check before I resolve", "brief me on this ticket", "ticket นี้ resolve ได้ยัง", "เช็คก่อน resolve", "อ่าน ticket นี้ให้หน่อย". Never changes the ticket, builds nothing. Not work-map (Decision tickets), not dual-verifier (one diff).'
effort: max
---

# Resolve the ticket

A ticket gets set to Resolved on "I think it is done". A week later it is reopened, because
one rule in its details had no passing test on that day. This skill stands at the two
moments where that is cheap to prevent: before the work starts, and before the State
changes.

**The failure this prevents:** a ticket resolved over a rule nobody tested, a pass that is
older than the last change, or a child task nobody did.

## What it never does

- It **builds nothing and fixes nothing.** The work between the two moments belongs to the
  other skills.
- It **never writes to the tracker** - no comment, no State change, no ticked box. The
  person does those.
- It **never writes a runbook.** A missing runbook is `guide-and-verify`'s to create.
- It **never starts the skill it names for a gap.** It names it and stops.

Its only write is one dated block appended to the ticket's runbook.

## The flow

```
 ┌──────────────────────────────────┐
 │ 0. Ask: briefing or check?       │
 │    Wait for the ticket URL       │
 └────────────────┬─────────────────┘
                  ▼
 ┌──────────────────────────────────┐
 │ 1. Read ticket, parent, children │
 │    (other links: title + State)  │
 └────────────────┬─────────────────┘
                  ▼
 ┌──────────────────────────────────┐
 │ 2. Find files by ticket number   │
 │    print the list, then read     │
 │    no runbook -> guide-and-verify│
 └───────┬──────────────────┬───────┘
         ▼                  ▼
 ┌───────────────┐  ┌───────────────────┐
 │ 3. BRIEFING   │  │ 4. CHECK          │
 │    chat only  │  │    rows + verdict │
 │    stop       │  │    append to the  │
 └───────────────┘  │    runbook        │
                    └───────────────────┘
```

## 0. Open - ask, and wait for the URL

Two things are needed: the **moment** (briefing or check) and the **ticket's URL**. Ask only
for what the invocation did not give, in one question:

> Briefing (before you start) or check (before you resolve)? And the ticket's URL, please.

Read nothing until you have the URL. A bare number is not enough - the URL names the
tracker, the organization and the project in one string, so the right number is never read
in the wrong project. Do not take the organization or project from an environment variable.

| URL | tracker |
|---|---|
| `dev.azure.com/<org>/<project>/_workitems/edit/<id>` | Azure DevOps |
| `github.com/<owner>/<repo>/issues/<n>` | GitHub Issues |
| anything else | say "I cannot read this tracker." and stop |

Then say one line: which moment this is, and for which ticket.

## 1. Read the ticket family

| who | how much |
|---|---|
| the ticket | in full |
| its direct parent | in full |
| every direct child | in full |
| predecessor, successor, related tickets | type, title and State only |
| the grandparent and above | not read |

**In full** means: type, title, State, revision, description (for an Azure DevOps Bug also
the repro steps), Acceptance Criteria, every comment, and **every attached image**. Fetch
one ticket the way `ticket-trace` does it - load that skill through your harness's
mechanism and follow its Operation B steps 4 and 5; images go through `read-picture`
(kind `requirement`). An image is often the whole requirement: never report "the
description is empty" without opening it.

The parent, the children, the other links and which States count as done are in
`references/ticket-family.md` - use its commands as written.

If you cannot reach the tracker, say so and ask the user to paste the ticket's fields. What
they paste is the ticket for this run; say in the output that it came through them.

## 2. Find the files, list them, read them

Search the project you run in for the ticket's number and each child's number:

1. file and folder names (`runbook-ado-151-…`, `151-…`, `ado-151-…`)
2. file contents (`#151`, `AB#151`, `ado-151`)
3. commit messages (`git log --grep`)
4. every file the ticket or the runbook names

Match the number whole: `151` does not match `1510`, a date or a GUID. Drop a hit that only
shares the digits.

Print the list before reading, grouped by kind:

```
Files for #151 (and child #297):
 runbook   documents/runbook-ado-151-overduereport-flow.md
 why       docs/why/151-loggingstatus-filter.md
 register  docs/why/requirements.md  (R-001)
 snapshot  documents/snapshots/ado-151-before/  (4 files)
 commits   7 with "151" in the message
```

Then read the documents. A snapshot folder is listed with its file count, not read file by
file.

**No runbook found.** Say so in one line, then hand off to `guide-and-verify` (load it
through your harness's mechanism) to create the runbook, giving it what you have already
read - the ticket, its parent and children, the file list - as its head start. It writes
the file in its own shape and the project's own naming. Do not write a runbook yourself, do
not use the parent's runbook, and do not go on as if there were none. Continue when the
runbook exists.

## 3. Moment one - the briefing

Chat only, in this order, then stop:

1. **The ticket** - one line: type, id, title, State, revision, URL.
2. **The family** - a table: parent, children, linked tickets, each with type, title, State.
3. **What it asks** - every AC line and every logic rule, quoted **as written**, each with
   a locator (`#151 AC-2`, `#151 description`, `#151 image <name>`).
4. **The files** - the list from step 2, and which to open first (the runbook, when it has
   steps).
5. **Open points** - an AC line that names something no file mentions; a linked ticket that
   is still open; a place where the ticket and its parent disagree.

Show a rule with logic the way the project asks for it (some projects fix a flowchart
shape in their `CLAUDE.md` / `AGENTS.md` - follow it). Write no file. Print no check table
and no verdict.

## 4. Moment two - the check

### 4.1 The rows

One row per:

- **AC line** - each Acceptance Criteria statement, one per clause that binds behaviour (a
  value, a condition, a trigger, a recipient, an ordering). A sentence with "and" between
  two obligations is two rows; a heading, an example or a rationale is none. The full rules
  are `why-this-logic`'s:
  `${CLAUDE_PLUGIN_ROOT}/skills/why-this-logic/references/splitting-rules.md`.
- **logic rule** - each decision point in the ticket's details: a filter, a threshold, a
  mapping, a default. Same splitting rules.
- **child** - each direct child ticket, with its State.

Quote each row as written, with its locator. Name them `AC-1`, `AC-2` … and `L-1`, `L-2` …
in the order the ticket has them; a child row is named by its id. When the project has
`docs/why/requirements.md` and the statement is registered there, put its ID beside the row.
Write the row list before you look for any test.

**A later check on the same ticket:** read the last `## Resolve check` block in the runbook
first. If the ticket's revision is the same, keep the rows; a row that was a pass is kept
only when its proof is still where the block says and it is not stale now - re-check every
other row. If the revision changed, split the rows again. An earlier block is never the
proof of a pass; the test result it points at is.

### 4.2 The result of one row

Ask these in order and stop at the first that decides:

```
 a test for this row?  ── none ───────────────▶ NO TEST
        │ yes
 its result?           ── fail ───────────────▶ FAIL
        │ pass
 older than the last
 change to the thing?  ── yes ────────────────▶ STALE
        │ no
 built as the ticket   ── yes ────────────────▶ PASS + mark
 says?                 ── no, written decision ▶ PASS - differs by decision
                       ── no, no decision ────▶ DIFFERS
```

**Where a test is found.** The runbook's steps and Outcome log, a ticket comment, a test
file in the repo, a case in a test-case suite, the register's *tested by* cell. Nothing
found: ask the user once, naming every such row - "Rows L-1 and AC-3 - no test found in the
runbook, the comments or the repo. Was either tested?"

**The mark on a pass - exactly one:**

| mark | proof |
|---|---|
| **cited** | a result written in the runbook, a ticket comment or a test file - give the locator and the date |
| **measured** | a test you ran in this session - give the command and its result line |
| **told** | the user says it was tested - write `told: <who>, <date>` |

A told pass counts. It is never shown as anything else.

**Stale.** Compare the pass's date with the last change you can see: a git commit on the
file (`git log -1 --format=%cI -- <file>`), a modified date written in the runbook or a
snapshot, the ticket's revision date. A pass older than the change is **stale**: show both
dates (`passed 2026-11-10; changed 2026-11-12`). It stops being stale when the test is run
again, or when the user says the change does not touch this row (then `told`). A pass with
no date cannot be compared: show `pass (no date)`. A change date that only the live system
holds needs one read-only query - write the exact query and ask once per query, per run:

> The last change to `<thing>` is only in the live system. This read-only query shows it:
> `<the query>`
> Run it? On no, the row shows "change date not checked".

Never write to a live system. A yes is for that one query.

**Differs.** Compare what the ticket says with what was built (the code, the flow
definition, a snapshot, the runbook's design). When they differ, look for a **written,
approved decision** that covers the difference - a runbook decision, an ADR, a ticket
comment, with who approved it. Found: `pass - differs by decision <id>`, with its locator,
when the test passes. Not found: **differs** - a passing test of the wrong rule is not a
pass. The user approving it now, in this session, closes the row as `told`.

**Child rows.** A child whose State is a done State (see `references/ticket-family.md`) is
`done`. Any other State is **open**, unless the user says it stays open on purpose - then
`open on purpose - told: <who>, <date>`. Do not check the child's own AC here.

### 4.3 The table and the verdict

Print in monospace:

```
row    what the ticket says        test   result
AC-1   runs Mon-Fri 08:00          S3c    pass   cited (runbook:255, 2026-11-09)
L-2    cut-off = UTC day - 7       S3c    pass   differs by decision D2 (runbook:70)
AC-3   PDF digest to admin         S6c    STALE  passed 2026-11-10; changed 2026-11-12
L-4    status Created or Partial   -      NO TEST
#297   child Task                  -      OPEN   State = New

READY TO RESOLVE: NO
```

| result | counts for READY |
|---|---|
| pass (cited / measured / told) | yes |
| pass - differs by decision | yes |
| child done, or open on purpose (told) | yes |
| no test, fail, stale, differs, open | no |

READY needs every row to count. When told rows or undated passes exist, the verdict reads
`READY TO RESOLVE: YES (N rows rest on your word)`. A linked ticket that is an open Bug is
pointed out in one line under the verdict; it does not change it.

### 4.4 On READY - draft the closing comment

Give the comment as raw Markdown in **one code block**, ready to paste. If the project's
`CLAUDE.md` / `AGENTS.md` fixes a comment format, use it. Otherwise:

```
## Ready to resolve - <date>, <time> UTC
Checked against the runbook and the repo (read-only).

| Item | Result |
|---|---|
| AC-1 <statement> | pass - cited (<locator>, <date>) |
| L-2 <statement> | pass - differs by decision <id> |
| AC-3 <statement> | pass - told (<who>, <date>) |

### Built differently from the ticket, by decision
- L-2: <what was built>, decision <id> (<locator>)

### Left open on purpose
- #<child>: <reason as the user gave it>

Details in the runbook: <path>
```

Leave out a `###` section that has no line. Then say:

> Paste this on the ticket, tick the acceptance criteria, and set the State yourself. I have
> changed nothing on the board.

### 4.5 On NOT READY - name the next skill, and stop

Draft no comment. Print at most one line per kind of gap, naming every row of that kind:

| gap | the line names |
|---|---|
| no test | `generating-test-cases` |
| fail | `debug-mantra` |
| stale | the test step to run again (or: say the change does not touch the row) |
| differs, no decision | `grill-then-plan` - the decision gets written first |
| open child | `resolve-the-ticket` on that child |

> L-4 has no test - write its case (`generating-test-cases`)?
> #297 is still New - run `resolve-the-ticket` on it, or say it stays open on purpose?

Then stop. Do not start any of them.

### 4.6 Record the check in the runbook

Append to the runbook, after its last section. Never edit a line above your own block:

```
## Resolve check - <date> <time UTC> - READY | NOT READY

Ticket #<id> rev <n>. Checked by resolve-the-ticket (read-only).

<the table of 4.3, as a Markdown table>

Gaps: <the lines of 4.5, or "none">
```

One block per check, newest last. Say the runbook's path.

## Rules that keep it honest

- **Read-only on the board, always.** No comment, no State, no tick.
- **One mark on every pass.** A pass with no mark is a row nobody can trust later.
- **A person's word is shown as a person's word.** `told` is never written as `cited`.
- **Stale is not a warning.** A warning beside READY is read as READY.
- **Quote, do not paraphrase.** A row is the ticket's own words with a locator.
- **Say what you could not read.** A tracker you could not reach, an image that would not
  open, a change date not checked - name it in the output, never inside a confident summary.

## Not this skill

| not this | because |
|---|---|
| `work-map` | it resolves a **Decision ticket** on a Decision map - a different thing |
| `dual-verifier` | two agents verify one finished task from its diff; no ticket, no AC rows |
| `why-this-logic` | traces each rule to its source and teaches it; its splitting rules and marks are used here, its phases are not run |
| `ticket-trace` | answers why one line exists; its ticket fetch is loaded here |
| `guide-and-verify` | owns the runbook; this skill only appends its check block |
| `generating-test-cases` | writes the test cases a `no test` row needs |

## Language

Mirror the language the user asked in - Thai in, Thai out. Keep identifiers, file paths,
the result words (`pass`, `no test`, `fail`, `stale`, `differs`, `open`), the three marks
and the verdict line in English.
````

- [ ] **Step 5: Verify the skill file**

```powershell
$f = 'plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md'
python -c "import sys,re; t=open(sys.argv[1],encoding='utf-8').read(); m=re.match(r'---\n(.*?)\n---\n', t, re.S); import yaml; d=yaml.safe_load(m.group(1)); print(d['name'], len(d['description']))" $f
Select-String -Path $f -Pattern 'CLAUDE_PLUGIN_ROOT' | ForEach-Object { $_.Line.Trim() }
Select-String -Path $f -Pattern 'Skill tool|AskUserQuestion|—' | Measure-Object | Select-Object -ExpandProperty Count
```

Expected: line 1 `resolve-the-ticket <N>` with N at or below 1024 (if `yaml` is not installed, run `pip install pyyaml` first; if N is above 1024, shorten the description's trigger list - keep the first sentence, the two moment words and the three "Not/Never" clauses); line 2 exactly one reference, `${CLAUDE_PLUGIN_ROOT}/skills/why-this-logic/references/splitting-rules.md`; line 3 `0` (no harness-specific tool name, no em dash).

- [ ] **Step 6: Walk the seven eval cases against the skill text**

For each case in `evals.json`, read its assertions and find the sentence in `SKILL.md` that makes each one true. Fix `SKILL.md` where an assertion has no sentence behind it. The pairs that must exist:

| eval | assertion | SKILL.md section |
|---|---|---|
| 0 | no comment drafted on NOT READY | 4.5 "Draft no comment" |
| 0 | child's own AC not checked | 4.2 "Do not check the child's own AC here" |
| 1 | verdict counts told rows | 4.3 "(N rows rest on your word)" |
| 2 | both dates shown | 4.2 Stale |
| 3 | passing test of the wrong rule is not a pass | 4.2 Differs |
| 4 | no file written at the briefing | 3 "Write no file" |
| 5 | no runbook -> guide-and-verify, parent's runbook not used | 2 "No runbook found" |
| 6 | nothing read before the URL; unknown tracker stops | 0 |

Expected: every row of this table points at a sentence that is present.

- [ ] **Step 7: Write the command wrapper**

`plugins/dev-workflows/commands/resolve-the-ticket.md`:

```markdown
---
description: Brief me on a ticket before the work starts, or check it before I set it to Resolved - every Acceptance Criteria line, logic rule and child ticket against a test, then READY or NOT READY. Read-only; never changes the ticket.
argument-hint: "[brief|check] <ticket URL - Azure DevOps or GitHub issue>"
---

Use the **`resolve-the-ticket`** skill for this.

Argument: $ARGUMENTS
```

- [ ] **Step 8: Commit**

```powershell
git add plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json plugins/dev-workflows/commands/resolve-the-ticket.md
git commit -m "feat(dev-workflows): resolve-the-ticket - a briefing before the work and a read-only check before the resolve (ADRs 0316-0329)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Playbook, router, manifests, generated tree

**Files:**
- Modify: `PLAYBOOK.md` (router diagram, table)
- Modify: `plugins/dev-workflows/skills/daily/SKILL.md` (description list, WORK table)
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json` (version, description, keywords)
- Modify: `.claude-plugin/marketplace.json` (dev-workflows version, description)
- Generated: `skills/resolve-the-ticket/`, `skills/daily/SKILL.md`

**Interfaces:**
- Consumes: skill name `resolve-the-ticket`, command `/dev-workflows:resolve-the-ticket` (Task 2).
- Produces: version `0.63.0` in both manifests; a clean `check_skills_tree.py`.

- [ ] **Step 1: Add the router edge to `PLAYBOOK.md`**

In the `flowchart TD` under `## WORKING — the situational router`, add this line directly after the line `    TT -. per-row, with a verdict .-> WTL`:

```
    WORK -- starting a ticket / about to resolve it --> RTT["resolve-the-ticket"]
```

- [ ] **Step 2: Add the table row to `PLAYBOOK.md`**

In the `| When… | Reach for |` table, add this row directly after the row that begins `| "is this condition / value right, and where does it come from?"`:

```markdown
| starting a ticket, or about to set it to Resolved - "resolve the ticket", "is this ticket ready to resolve", "ticket นี้ resolve ได้ยัง", "brief me on this ticket" | `resolve-the-ticket` (`/dev-workflows:resolve-the-ticket`) - asks briefing or check and waits for the ticket URL (Azure DevOps or GitHub Issues). Briefing: the ticket, its parent and children, linked tickets, the runbook and the files to open. Check: one row per AC line, logic rule and child - pass (cited / measured / told), no test, fail, stale, differs, open - then READY or NOT READY; on READY a closing comment to paste, on NOT READY the next skill per gap. Never changes the ticket, builds nothing; the check is appended to the ticket's runbook. Not `work-map` (Decision tickets) or `dual-verifier` (one diff) (ADRs 0316-0329) |
```

- [ ] **Step 3: Add the skill to the `/daily` router**

In `plugins/dev-workflows/skills/daily/SKILL.md`:

(a) in the frontmatter `description`, replace `dual-verifier, drive-to-legacy, crm-archaeology, generating-test-cases), findings-to-ado-backlog or` with `dual-verifier, drive-to-legacy, crm-archaeology, generating-test-cases, resolve-the-ticket), findings-to-ado-backlog or`

(b) in the `### 2. WORK` table, add this row directly after the row `| asking why code/a ticket exists | `ticket-trace` |`:

```markdown
| starting a ticket, or about to set it to Resolved | `resolve-the-ticket` — a briefing before the work, a read-only check before the resolve |
```

- [ ] **Step 4: Re-check the version's global max, then bump both manifests**

```powershell
git for-each-ref --format='%(refname:short)' refs/heads refs/remotes | ForEach-Object { (git show "${_}:plugins/dev-workflows/.claude-plugin/plugin.json" 2>$null | Select-String '"version"').Line } | Sort-Object -Unique
```

Expected: the highest value printed is `0.62.0`. Use that max + 1 minor (`0.63.0`); if a higher value prints, use its minor + 1 instead in every edit below.

In `plugins/dev-workflows/.claude-plugin/plugin.json`:
- `"version": "0.62.0"` -> `"version": "0.63.0"`
- the `description` value ends with `ADRs 0175-0208).` - replace that ending with: `ADRs 0175-0208). Plus RESOLVE-THE-TICKET (/dev-workflows:resolve-the-ticket: a briefing before the work on a ticket and a read-only check before a person sets it to Resolved - every Acceptance Criteria line, logic rule and child ticket against a test, marked cited / measured / told, a stale pass and an undecided difference kept NOT READY, the closing comment drafted for the person to paste; Azure DevOps and GitHub Issues; never writes to the tracker. ADRs 0316-0329).`
- in `keywords`, after `"flowchart-node"` add `"resolve-the-ticket"`, `"ready-to-resolve"`, `"acceptance-criteria"`, `"ticket-briefing"` (add a comma after `"flowchart-node"`).

In `.claude-plugin/marketplace.json`, in the `dev-workflows` entry (the object with `"source": "./plugins/dev-workflows"`):
- `"version": "0.62.0"` -> `"version": "0.63.0"`
- the `description` value ends with `refuses to claim their English improved.)` - replace that ending with: `refuses to claim their English improved.) Plus resolve-the-ticket: a briefing before the work on a ticket and a read-only check before it is set to Resolved - every acceptance criterion, logic rule and child ticket against a test; never writes to the tracker.`

Verify:

```powershell
python -c "import json; p=json.load(open('plugins/dev-workflows/.claude-plugin/plugin.json',encoding='utf-8')); m=json.load(open('.claude-plugin/marketplace.json',encoding='utf-8')); e=[x for x in m['plugins'] if x['name']=='dev-workflows'][0]; print(p['version'], e['version'], 'resolve-the-ticket' in p['description'], 'resolve-the-ticket' in e['description'], 'resolve-the-ticket' in p['keywords'])"
```

Expected: `0.63.0 0.63.0 True True True`

- [ ] **Step 5: Regenerate the skills tree and check it**

```powershell
python scripts/generate_skills_tree.py
python scripts/check_skills_tree.py
git status --short skills/
```

Expected: the checker exits `0` with no findings. `git status` shows `?? skills/resolve-the-ticket/` and ` M skills/daily/SKILL.md`; ` M skills/guide-and-verify/SKILL.md` was already modified by the other session before this plan and must be left exactly as the generator leaves it - do not stage it. If any OTHER path under `skills/` shows a change, stop and report it; do not stage it.

```powershell
Get-ChildItem skills/resolve-the-ticket -Recurse -Name
```

Expected: `SKILL.md`, `evals\evals.json`, `references\ticket-family.md`, and the copies the generator resolved for the two plugin-root references (`why-this-logic`'s `splitting-rules.md`, `ticket-trace`'s `ado.md`) wherever the generator places them. If the checker reports an unresolved `${CLAUDE_PLUGIN_ROOT}` reference, read its message, correct the path in the source file under `plugins/` (never under `skills/`), and run both scripts again.

- [ ] **Step 6: Run the repo's own checks**

```powershell
python scripts/check_skills_tree.py; "exit: $LASTEXITCODE"
python plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict; "exit: $LASTEXITCODE"
python -m pytest scripts -q
```

Expected: both `exit: 0`; pytest reports all passed. (The vendored check is unaffected by this plan; a non-zero exit there is the other session's change to report, not to fix.)

- [ ] **Step 7: Commit**

```powershell
git add PLAYBOOK.md plugins/dev-workflows/skills/daily/SKILL.md plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json skills/resolve-the-ticket skills/daily/SKILL.md
git status --short
```

Expected: only those paths staged; the other session's five files unstaged.

```powershell
git commit -m "chore(dev-workflows): 0.62.0 -> 0.63.0 - resolve-the-ticket in the playbook, the /daily router, both manifests and the skills tree (ADR 0329)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 8: Final re-check of the minted numbers before any merge or push**

```powershell
git fetch --all --quiet
git for-each-ref --format='%(refname:short)' refs/remotes | ForEach-Object { git ls-tree -r --name-only --full-tree $_ -- docs/adr } | Select-String -Pattern '-(031[6-9]|032[0-9]|033[0-3])-' | Sort-Object -Unique
git for-each-ref --format='%(refname:short)' refs/remotes | ForEach-Object { (git show "${_}:plugins/dev-workflows/.claude-plugin/plugin.json" 2>$null | Select-String '"version"').Line } | Sort-Object -Unique | Select-Object -Last 1
```

Expected: no ADR line from a remote ref; the highest remote version is below `0.63.0`. If either fails, stop and report - a renumber is the user's call. Do not push or merge; that is the user's decision.
