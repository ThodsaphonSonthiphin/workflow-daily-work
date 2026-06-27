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

**Document skill**:
A skill whose output is a durable Markdown artifact (ARCHITECTURE.md, post-mortem,
design spec, audit, trace). Always includes Mermaid diagrams (ADR 0005/0006).
_Avoid_: study skill (narrower), doc generator.

**Channel output**:
Skill output shaped for a delivery channel (Slack, JIRA comment, email, standup line,
Tribletext) rather than a repo document. Exempt from the diagram convention; a document
skill posting to a channel asks before stripping diagrams (ADR 0006).
_Avoid_: chat output, message.

**Diagram convention**:
The rule that every skill-generated Markdown document opens with one overview Mermaid
diagram, adds type-matched diagrams per section (sequence = flow, er = data,
flowchart = decision, graph = hierarchy), and that ADRs carry a small decision diagram
(ADRs 0005–0009). Governs **Markdown-document** output only; an interactive skill whose
output is a live terminal session follows the sibling **Terminal diagram** rule instead
(ADR 0010). Canonical wording: `plugins/dev-workflows/references/diagram-convention.md`.
_Avoid_: UML rule (it's the Mermaid family, not strict UML class diagrams).

**Terminal diagram**:
A text / box-drawing diagram authored to read in a monospace **terminal** session, used by
an **interactive skill** whose output is a live chat session rather than a `.md` document
(e.g. debug-mantra's four-step process diagram). Unicode box-drawing, vertical layout,
emitted inside a fenced code block. The terminal sibling of the **Diagram convention** —
introduced because Mermaid fences don't render in a terminal (ADR 0010). Canonical wording
lives alongside the Mermaid rules in
`plugins/dev-workflows/references/diagram-convention.md`.
_Avoid_: ASCII art (too generic), UML diagram (not class-diagram UML), Mermaid diagram.

**Term drill-down**:
A mechanism in a `problem-description` walkthrough by which the reader clicks an
unfamiliar term in the narration to open a **side drawer** showing a short definition —
sourced from this repo's `CONTEXT.md` glossary and inlined into the self-contained HTML
at authoring time (ADR 0017) — with **see-also** links that hop to related terms,
swapping the drawer per hop. Cross-cutting: it applies to every walkthrough mode, not a
mode of its own (ADRs 0016, 0018). The drawer code is kept DRY in one reference file
(`references/term-drilldown.html`) and inlined at generation (ADR 0019). Makes a
walkthrough *glossary-aware*.
_Avoid_: tooltip (narrower — can't hop), glossary popup, nested sub-walkthrough.

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
