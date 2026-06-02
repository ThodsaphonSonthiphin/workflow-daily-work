---
description: Check that everything needed for the ado-backlog toolkit is installed and configured (Azure CLI + login, .NET 10 SDK, Python + openpyxl, target org/project). Run this first on a new machine or when ADO calls fail with auth errors.
---

Run the prerequisite checker and report the results, then help me fix anything that fails.

Execute (PowerShell):

```
powershell -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check.ps1"
```

For each `FAIL` line, give me the exact command to fix it. If everything passes, tell me I'm
ready and remind me of the one-shot command: `/ado-backlog:run <my-findings-file>`.
