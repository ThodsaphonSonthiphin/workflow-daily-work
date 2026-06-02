# ado-backlog — 1-page quickstart

## First time on this machine
```text
1. az login                                   # sign in to Azure DevOps
2. /plugin marketplace add ThodsaphonSonthiphin/workflow-daily-work   # add the marketplace (once)
3. /plugin install ado-backlog@workflow-daily-work
4. /ado-backlog:setup-check                   # verify .NET 10, Python+openpyxl, org/project
```
Set your board (or let the skill ask):
```text
$env:AZDO_ORG = "Cartagena365"
$env:AZDO_PROJECT = "GlassHull"
```

## Every time — one command
```text
/ado-backlog:run "C:\path\to\findings.xlsx"
```
Then just answer the prompts:
1. **Column mapping** — which column is the key/current/expected/severity.
2. **Scope** — which findings to file now (default: Critical + confirmed first).
3. **Assignment** — unassigned (default), you, or a teammate's email.
4. **Estimates** — Claude proposes hours per item (created as child Tasks); adjust any, confirm.
5. **Dry-run** — you'll see exactly what will be created. **Approve to create.**
6. Done — ticket links are written back into your spreadsheet.

> Nothing is created in Azure DevOps until you approve the dry-run.

## See your own work (daily "what's on my plate")
```text
/ado-backlog:my-work                             # grouped table, clickable ticket #, open work first
```

## Use one piece on its own
```text
/ado-backlog:extract-findings "report.csv"     # just normalize a source
/ado-backlog:ado-create-work-items "backlog_input.json"   # just create from a prepared file
/ado-backlog:ado-auth                            # just check / fix the ADO token
```

## When something breaks
| Symptom | Fix |
|---|---|
| `401 Unauthorized` | `az login` (token expired) |
| `403 Forbidden` | PAT scope / board permissions |
| `potentially dangerous Request.Path (:)` | `AZDO_ORG` was a full URL — use just the org **name** |
| dry-run `FAIL` on a type | that type doesn't exist on your project's process — re-run classify |
| created duplicates | don't re-run the real create without write-back; prune already-filed rows |

Full docs: [`README.md`](README.md) · contracts: [`references/data-contracts.md`](references/data-contracts.md)
