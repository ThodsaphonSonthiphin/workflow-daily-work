# Ticket family - parent, children, links, done State

Read-only commands for the part of a ticket read that `ticket-trace` does not carry. The
token, one work item's fields, its comments and its attached images are in
the `ticket-trace` skill's `references/ado.md` (load that skill through your harness's mechanism) - use those as written.

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
| `System.LinkTypes.Dependency-Forward` | successor (not observed in the measurement) | type, title, State |
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

A State name differs by process (Resolved, Closed, Done). Read the category first; the State named `Resolved` also counts (ADR 0330):

```powershell
(Invoke-RestMethod -Headers @{Authorization="Bearer $token"} -Uri 'https://dev.azure.com/{org}/{project}/_apis/wit/workitemtypes/{type}/states?api-version=7.0').value | ForEach-Object { '{0}  ->  {1}' -f $_.name, $_.category }
```

URL-encode a type with a space (`User%20Story`). A child is **done** when its State's
category is `Resolved` or `Completed`, **or** its State is named `Resolved` whatever its
category (ADR 0330). `Removed` is not done and not open: show it as `removed` and leave it
out of the verdict.

Measured: 2026-11-16, MackayGoodwin/Elevate, type User Story - New -> Proposed, Active ->
InProgress, Resolved -> InProgress, Closed -> Completed, Removed -> Removed. In this
process the State named `Resolved` has category `InProgress`, not `Resolved` - which is why
the name `Resolved` counts as done on its own (ADR 0330). Done here: `Resolved`, `Closed`.

## GitHub Issues - parent, children, links

```powershell
gh issue view {n} --repo {owner}/{repo} --json number,title,state,body,comments,updatedAt
gh api --paginate "repos/{owner}/{repo}/issues/{n}/sub_issues" --jq '.[] | [.number,.state,.title] | @tsv'
gh api "repos/{owner}/{repo}/issues/{n}/parent" --jq '[.number,.state,.title] | @tsv'
```

Keep the `--jq` filter free of double quotes (use `@tsv`): Windows PowerShell 5.1 splits a
filter with a quoted string inside it into two arguments and `gh` fails with
`accepts 1 arg(s), received 2`.

`--paginate` is required on the sub-issues read: the API returns 30 rows a page, and a child on page two would be missed.

`updatedAt` stands in for the revision on GitHub (it changes on any edit or comment): the
check block records it as `updated <timestamp>`, and a later run re-splits the rows when it
has changed.

The parent call answers HTTP 404 when the issue has no parent - that is "no parent", not a
failure. Other links are the `#<number>` mentions in the body and the comments: read each
with `gh issue view <number> --repo {owner}/{repo} --json number,title,state`.

Acceptance Criteria on GitHub are a task list (`- [ ] ...`) or the lines under a heading
that reads "Acceptance criteria" in the body. Neither found: say "no AC section in the
issue" - never invent the lines from the title.

Measured: 2026-11-16, ThodsaphonSonthiphin/workflow-daily-work #15 (label
`decision-map:map`) - `gh issue view --json` answered number 15, state OPEN, 0 comments,
a body of 9951 characters; `gh api --paginate .../sub_issues` answered 16 rows, #16, #17
and #18 among them, each `closed`, states overall `closed` and `open`; `parent` on #15 answered HTTP 404 `No parent issue found` (exit code 1); `parent`
on #16 answered #15 `open`. `gh issue view 15 --json number,updatedAt --jq '[.number,.updatedAt] | @tsv'`
answered `15  2026-09-07T06:01:46Z`.

## GitHub Issues - done State

`state` is `open` or `closed`. A child is **done** when it is `closed`.

Measured: 2026-11-16, ThodsaphonSonthiphin/workflow-daily-work #15 - the sub-issues
answered `closed` or `open` only, lower case.

## The last edit to the requirement text

A pass is stale against the ticket only when the ticket's requirement text changed after it
- its description, Acceptance Criteria or repro steps (ADR 0331). A comment, a tag, a State
change or an assignment is not such an edit, so the revision number alone is not the date
to compare with.

Azure DevOps - keep only the updates that touch one of the three fields, and take each
one's date from `System.ChangedDate`:

```powershell
(Invoke-RestMethod -Headers @{Authorization="Bearer $token"} -Uri 'https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{id}/updates?api-version=7.0').value | Where-Object { $_.fields.'System.Description' -or $_.fields.'Microsoft.VSTS.Common.AcceptanceCriteria' -or $_.fields.'Microsoft.VSTS.TCM.ReproSteps' } | ForEach-Object { '{0}  rev {1}  {2}' -f $_.fields.'System.ChangedDate'.newValue, $_.rev, (($_.fields.PSObject.Properties.Name | Where-Object { $_ -in 'System.Description','Microsoft.VSTS.Common.AcceptanceCriteria','Microsoft.VSTS.TCM.ReproSteps' }) -join ',') }
```

The last line printed is the last edit to the requirement text. Do not take the date from
the update's `revisedDate`: it is the moment that revision was replaced by the next one, and
on the latest revision it is the far-future sentinel `9999-01-01T00:00:00Z`.

Measured: 2026-11-16, MackayGoodwin/Elevate #151 (25 updates, current rev 20) - three
updates touch the requirement text: rev 1 `System.Description` (ChangedDate
2026-10-27T00:30:30Z), rev 6 `Microsoft.VSTS.Common.AcceptanceCriteria,System.Description`
(ChangedDate 2026-10-30T02:50:14Z, while its `revisedDate` read 2026-11-09T03:21:36Z) and
rev 13 `System.Description` (ChangedDate 2026-11-10T03:26:10Z). The last edit to the
requirement text is 2026-11-10T03:26:10Z at rev 13; revs 14-20 changed the State, the
stack rank and two comments (revs 16, 17: `System.History`) only.
The last update's `revisedDate` read `9999-01-01T00:00:00Z`. `System.ChangedDate.newValue`
is the field that gave a real edit date.

GitHub - `lastEditedAt` is the last edit to the issue body; it is null when the body was
never edited, and then the creation date `createdAt` is the last requirement edit. Keep the
query free of double quotes (Windows PowerShell 5.1):

```powershell
gh api graphql -F o={owner} -F r={repo} -F n={n} -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){lastEditedAt updatedAt createdAt}}}'
```

Measured: 2026-11-16, ThodsaphonSonthiphin/workflow-daily-work #15 - `lastEditedAt`
2026-09-07T06:01:46Z, `updatedAt` 2026-09-07T06:01:46Z, `createdAt` 2026-09-06T23:32:09Z.
A null `lastEditedAt` was not observed in this measurement.

## Gotchas

- 401 / 403 on Azure DevOps: the token is expired or from the wrong account - `az login`
  with the work account, then read the token again.
- 404 on a work item: the number is in another project. Check the URL; do not try other
  projects.
- A relation whose `url` contains `/_apis/wit/attachments/` or starts `vstfs:` is a file or
  a commit, not a ticket.
