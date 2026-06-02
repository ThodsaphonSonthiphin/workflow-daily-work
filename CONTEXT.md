# ADO Backlog Toolkit

A Claude Code plugin that turns findings (audits, spreadsheets, pasted lists) into
Azure DevOps work items, and surfaces a person's assigned work — authenticating to
Azure DevOps and pointing every step at the right place to read and write.

## Language

**Organization**:
An Azure DevOps organization, referenced everywhere by its **bare name** (e.g.
`Cartagena365`) — the single segment after `dev.azure.com/`. It is **not** a URL, and
**not** the Azure subscription or Entra tenant the account signs into (`az account show`
returns the latter, which is a different thing). Carried as `AZDO_ORG`.
_Avoid_: org URL, Azure subscription, tenant, account.

**Project**:
A project inside an Organization (e.g. `GlassHull`), referenced by name (exact casing).
A work item type is only valid relative to the project's **process** (Agile, Scrum,
Basic, CMMI). Carried as `AZDO_PROJECT`.
_Avoid_: team project, board, repo.
