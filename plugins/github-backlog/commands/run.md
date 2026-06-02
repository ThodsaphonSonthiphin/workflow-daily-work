---
description: Run the full findings -> GitHub Issues process on a file or pasted text. Extract findings, triage, classify by labels and milestone, visual dry-run, then create on approval and write issue links back. Use whenever someone wants to turn an audit/spreadsheet/list of issues into GitHub Issues.
argument-hint: "[path-to-findings-file]"
---

Use the **`findings-to-github-issues`** skill to turn the input below into a GitHub Issues backlog.

Input: $ARGUMENTS

Follow the skill end to end, and **stop at the visual dry-run gate** — show me exactly what will be
created and wait for my explicit approval before creating anything in GitHub.
