# Workflow Daily Work Context

Glossary and core terms for this Claude Code plugin marketplace. The repository contains
multiple plugins, including ADO backlog automation, GitHub backlog automation, and
general development workflow skills.

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

## Repo architecture terms

**Marketplace**:
The repo as a whole — a Claude Code plugin marketplace declared in
`.claude-plugin/marketplace.json`. It _lists_ plugins; it is not a plugin itself.
_Avoid_: repo (ambiguous), package.

**Plugin**:
A self-contained unit a colleague installs (e.g. `ado-backlog`), defined by its own
`.claude-plugin/plugin.json`. Bundles skills, commands, scripts, and references.

**Skill**:
A single reusable capability under `skills/<name>/SKILL.md`, model-invoked by its
`description` triggers. One pipeline step = one skill.
_Avoid_: command (a command is a thin user-typed entry point, not the capability).

**Command**:
A user-typed `/ado-backlog:<name>` entry point under `commands/<name>.md`; a thin
wrapper that hands off to a skill. Not where logic lives.

**Orchestrator**:
The one skill (`findings-to-ado-backlog`) that sequences the other skills end-to-end
and enforces the safety gates. A skill, but the conductor — not a peer step.

**Data contract**:
One of the three JSON files (`findings.json`, `backlog_input.json`,
`backlog_result.json`) that carry state between steps, joined by a stable `key`.
Canonical shapes live in `references/data-contracts.md` — that file is the source of
truth; nothing else redefines them.

**Safety gate**:
A deliberate stop before an irreversible action: dry-run before real create, explicit
user approval before any write, back up the source before write-back.

## GitHub terms (github-backlog plugin)

**GitHub Owner**:
The org or user name segment of a GitHub repo URL (e.g. `Cartagena365`). Carried as
`GH_OWNER`. It is **not** a URL. Mirrors `AZDO_ORG` from the ADO side.
_Avoid_: org URL, full repo path.

**GitHub Repo**:
The repository name (e.g. `GlassHull`). Carried as `GH_REPO`. Mirrors `AZDO_PROJECT`.
_Avoid_: repo URL, full path.

**Tracking Issue**:
A GitHub Issue whose body contains a task list (`- [ ] #N title`) linking all issues
created in a batch. GitHub renders it as a progress bar. The GitHub equivalent of an
ADO Feature/Epic parent item.
_Avoid_: epic issue (ambiguous), parent issue (not a GitHub term).

**Size label**:
A `size:XS` / `size:S` / `size:M` / `size:L` / `size:XL` label on a GitHub Issue
encoding the effort estimate for that item. Maps from raw hours during classification.
_Avoid_: story points (different concept), estimate label.
