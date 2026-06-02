---
description: Run the full findings -> Azure DevOps backlog process on a file or pasted text. Extract findings, triage, classify by the project's process, dry-run, then create on approval and write ticket links back. Use whenever someone wants to turn an audit/spreadsheet/list of issues into ADO work items.
argument-hint: "[path-to-findings-file]"
---

Use the **`findings-to-ado-backlog`** skill to turn the input below into an Azure DevOps backlog.

Input: $ARGUMENTS

Follow the skill end to end, and **stop at the dry-run gate** — show me exactly what will be
created and wait for my explicit approval before creating anything in Azure DevOps.
