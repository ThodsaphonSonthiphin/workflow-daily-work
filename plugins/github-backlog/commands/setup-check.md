---
description: Verify all prerequisites for the github-backlog pipeline — gh CLI, Python, requests, openpyxl, GH_OWNER/GH_REPO env vars, and repo reachability. Read-only.
argument-hint: ""
---

Use the **`github-auth`** skill to run the setup checker:

```powershell
powershell -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check_github.ps1"
```

Report any FAIL lines with their fix. WARN lines (missing env vars) are OK before the pipeline starts.
