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

Measured: 2026-11-16, MackayGoodwin/Elevate #151 - rev 20; six relations, one line each:
`System.LinkTypes.Hierarchy-Reverse` 147 `Parent`; `System.LinkTypes.Hierarchy-Forward` 297
`Child`; `System.LinkTypes.Dependency-Reverse` 272 `Predecessor`; `System.LinkTypes.Related`
295, 150 and 145, each `Related`. The batch read of 272, 295, 150, 145 returned one row
each: #272 User Story New, #295 Bug Resolved, #150 User Story Resolved, #145 User Story
Resolved.

## Azure DevOps - which States are done

A State name differs by process (Resolved, Closed, Done). Read the category, not the name:

```powershell
(Invoke-RestMethod -Headers @{Authorization="Bearer $token"} -Uri 'https://dev.azure.com/{org}/{project}/_apis/wit/workitemtypes/{type}/states?api-version=7.0').value | ForEach-Object { '{0}  ->  {1}' -f $_.name, $_.category }
```

URL-encode a type with a space (`User%20Story`). A child is **done** when its State's
category is `Resolved` or `Completed`, **or** its State is named `Resolved` whatever its
category (ADR 0307). `Removed` is not done and not open: show it as `removed` and leave it
out of the verdict.

Measured: 2026-11-16, MackayGoodwin/Elevate, type User Story - New -> Proposed, Active ->
InProgress, Resolved -> InProgress, Closed -> Completed, Removed -> Removed. In this
process the State named `Resolved` has category `InProgress`, not `Resolved` - which is why
the name `Resolved` counts as done on its own (ADR 0307). Done here: `Resolved`, `Closed`.

## GitHub Issues - parent, children, links

```powershell
gh issue view {n} --repo {owner}/{repo} --comments
gh api "repos/{owner}/{repo}/issues/{n}/sub_issues" --jq '.[] | [.number,.state,.title] | @tsv'
gh api "repos/{owner}/{repo}/issues/{n}/parent" --jq '[.number,.state,.title] | @tsv'
```

Keep the `--jq` filter free of double quotes (use `@tsv`): Windows PowerShell 5.1 splits a
filter with a quoted string inside it into two arguments and `gh` fails with
`accepts 1 arg(s), received 2`.

The parent call answers HTTP 404 when the issue has no parent - that is "no parent", not a
failure. Other links are the `#<number>` mentions in the body and the comments: read each
with `gh issue view <number> --repo {owner}/{repo} --json number,title,state`.

Acceptance Criteria on GitHub are a task list (`- [ ] ...`) or the lines under a heading
that reads "Acceptance criteria" in the body. Neither found: say "no AC section in the
issue" - never invent the lines from the title.

Measured: 2026-11-16, ThodsaphonSonthiphin/workflow-daily-work #15 (label
`decision-map:map`) - `gh issue view` answered number 15, state OPEN; `sub_issues`
answered 16 rows, #16, #17 and #18 among them, each `closed`, states overall `closed` and
`open`; `parent` on #15 answered HTTP 404 `No parent issue found` (exit code 1); `parent`
on #16 answered #15 `open`.

## GitHub Issues - done State

`state` is `open` or `closed`. A child is **done** when it is `closed`.

Measured: 2026-11-16, ThodsaphonSonthiphin/workflow-daily-work #15 - the sub-issues
answered `closed` or `open` only, lower case.

## Gotchas

- 401 / 403 on Azure DevOps: the token is expired or from the wrong account - `az login`
  with the work account, then read the token again.
- 404 on a work item: the number is in another project. Check the URL; do not try other
  projects.
- A relation whose `url` contains `/_apis/wit/attachments/` or starts `vstfs:` is a file or
  a commit, not a ticket.
