---
description: Show my assigned Azure DevOps work items as a grouped table with clickable ticket links — open work first, sorted by priority. The daily "what's on my plate / read the task hub" view.
---

Use the **my-work** skill to list the work items assigned to me as a grouped table.

Run (PowerShell):

```
dotnet run "${CLAUDE_PLUGIN_ROOT}/scripts/my-work.cs"
```

Needs `az login` and `$env:AZDO_ORG`. Add `$env:AZDO_SHOW_DONE="true"` to include completed
items. After it prints, point out the top actionable item per project and ask what I want to
do next.
