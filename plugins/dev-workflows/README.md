# dev-workflows

General-purpose **development workflow skills** — the reusable, non-domain-specific
helpers that support day-to-day engineering work. This plugin is a growing collection;
more skills will be added over time.

## Skills

| Skill | What it does |
|---|---|
| `grill-then-plan` | A domain-aware **grilling session**: interviews you one question at a time, challenges your plan against the project glossary, sharpens fuzzy terms, and captures decisions inline (`CONTEXT.md` + ADRs). Writes a design spec, then **hands off to `superpowers:writing-plans`** to produce the implementation plan. |
| `problem-description` | Generate a self-contained **interactive HTML walkthrough** that explains a complex technical problem (DB error, race condition, design issue) with concrete data and manual step-through navigation. Two modes: **diagram** (boxes + data flow) and **tables** (grid state changes). |
| `management-talk` | Reshape engineer-to-engineer content for **engineering-org leadership** (VPs, directors, PMs, release managers) and **shape it for the channel** — JIRA comment, Slack post, async standup line, email, or meeting talking-points. Keeps product names/tickets/PRs, strips code identifiers, translates mechanism into plain cause-and-effect. |
| `fit-gap-analysis` | Compare a **target** (spec, product vision, competitor, RFP, "to-be") against a **system as actually built**. Produces an evidence-first **capability matrix** + step-by-step **user-journey comparison**, verified against the **live system** (schema + code, not docs), rolled up into **decisions**. Stack-agnostic. |
| `study-design-verify` | Evidence-grounded **advisory pipeline** for *"how should this work?"* questions about any real system. **Study** (parallel readers → structured, citable findings; live access read-only with an evidence trail) → **Design** (3 independent designers with conflicting value systems) → **Verify** (an adversarial reviewer attacks every design against the live schema, code, and usage data) → a **phased recommendation** with explicit "what NOT to do" entries. |
| `daily` | **The one command to remember.** Hybrid router into the daily arc: bare `/daily` shows the 5-station menu (start / work / file / report / wrap); `/daily <station>` jumps straight there. Routes to the right skill and never errors on unknown input. |
| `debug-mantra` | Four-mantra **debugging discipline** — reproduce, trace the fail path, falsify the hypothesis, cross-reference every breadcrumb — applied in order before proposing any fix. Opens with a **terminal process diagram** of the four steps (incl. the escalation ladder, the no-repro STOP gate, and the loop-back) so the discipline is scannable at a glance. |
| `post-mortem` | Write the **canonical engineering record of a fixed bug** — root cause, mechanism, fix, validation, and how it slipped through. Engineer-audience; run after a debug session lands a fix. |
| `scrutinize` | **Outsider-perspective review** of a plan, PR, or change: first questions intent and simpler alternatives, then traces the actual code path to verify the change does what it claims. |
| `dual-verifier` | **Independent verification** of completed work: two subagents run the same checks independently; findings are merged, deduplicated, and ranked by severity and confidence. |
| `drive-to-legacy` | Systematic exploration of an **unfamiliar legacy codebase** — for studying, documenting, onboarding, or preparing a port/migration. |
| `crm-archaeology` | Study a **live Dynamics 365 / Dataverse org** end-to-end and produce one ARCHITECTURE.md — pulls every customization to disk (entities, forms, JS/React web resources, PCF, workflows, plugins, flows, classic + modern commands, security), maps every business entity (standard AND custom), then traces business processes layer by layer. Read-only by design. The org-side sibling of `drive-to-legacy`. |
| `invoice-generator` | Read git commits across workspace repos into a **daily work summary**, then always reshape it for the target channel via `management-talk` (Tribletext entry, Slack, standup, email, JIRA, talking-points). |
| `naming-audit` | Verify a list of claimed labels/values/mappings **against the authoritative system of record**, item by item — verdict card + the exact app/code path to check. Source-of-truth wins. |
| `ticket-trace` | Two-way **commit ↔ ticket traceability**: commits always carry their ticket number, and "why was this changed?" walks `git blame` → commit → ticket → tracker (incl. attached images). |

Each is invoked automatically by its trigger phrases, or explicitly via the `Skill` tool.

## grill-then-plan

Use when you want **both** a rigorous design conversation **and** a written implementation
plan afterward.

```
explore context → grill one question at a time → capture terms/ADRs inline
   → write design spec → (on approval) hand off to superpowers:writing-plans
```

- Domain-aware: cross-references your code and `CONTEXT.md`, surfaces contradictions.
- Captures as it goes: glossary terms land in `CONTEXT.md`, hard-to-reverse trade-offs
  become ADRs under `docs/adr/`.
- Spec goes to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`.

> **Requires the [superpowers](https://github.com/anthropics/claude-plugins-official) plugin.**
> The skill does a preflight check and offers to install it if missing — the final handoff to
> `superpowers:writing-plans` cannot run without it.
>
> If you only want the grilling/docs *without* a plan, stop after the design-spec step — the spec, CONTEXT.md updates, and ADRs are already written by then.

## problem-description

Use when an interactive artifact would explain a problem better than prose — the reader
controls the pace (`Next →` / `← Previous` / `↻ Reset`) and can point at any element and
understand why it is in its current state.

- **Mode A — diagram** (default): components positioned spatially, arrows fire between them
  with flying value labels. Best for architecture, data flow, concurrency, locking.
- **Mode B — tables**: a grid whose cells change state per step. Best for row/record-level
  problems, query results, state machines.

Ships two starter templates the skill reads and adapts:
[`skills/problem-description/template-diagram.html`](skills/problem-description/template-diagram.html)
and [`skills/problem-description/template.html`](skills/problem-description/template.html).

## management-talk

Use when engineering work needs to flow **up the org or sideways into product/release** —
a status update for leadership, not for the team.

- **Audience:** engineering-savvy non-engineers. They read product names, JIRA keys, and
  PR numbers; they do not read code.
- **Channel-shaped:** the same diagnosis becomes a full structured JIRA comment, a tight
  Slack post, a one-line standup note, an exec email, or spoken meeting bullets — you pick
  the channel and it formats to fit.
- **Translates, doesn't dumb down:** keeps concept-level vocabulary (race, regression,
  uninitialized buffer), strips function names / file paths / SHAs, and turns mechanism into
  plain cause-and-effect — without promoting a speculation to a finding.
- Print-only by default; it never posts to Slack/email, and only back-posts to JIRA on
  explicit approval.

## fit-gap-analysis

Use when comparing a **target** (spec, product vision, competitor, RFP, "to-be") against a
**system as actually built** — *"how far are we, what changes, what's the impact?"*.

- **Evidence-first:** every verdict cites something real in the **live** system (a field, an
  endpoint, a `file:symbol`, a live count) — never the docs, which drift.
- **Two lenses:** a **capability matrix** (does X exist — Fit / Partial / Gap / **Mismatch**)
  *and* a **journey comparison** (step-by-step Target vs Actual) that catches flow divergences
  a checklist misses (wrong entry point, missing step, same feature wired differently).
- **Decisions, not lists:** each row gets a **Cluster** (Reuse / Rework / Build-new / Mixed)
  + Effort, so dozens of gaps roll up into the few choices a meeting can act on.
- **Stack-agnostic:** adapts the "extract live ground truth" step to the platform — DB schema,
  OpenAPI, a metadata endpoint, running config, the deployed bundle, or live cloud state.

## study-design-verify

Use when the user wants a **recommendation that must survive scrutiny** about an existing
system — *"how should A convert/map/migrate to B?"*, *"study my business, then advise"*,
*"should we copy, link, or recalculate this data?"*. Works against any stack: codebase,
database, CRM/ERP, SaaS, API, data pipeline.

The core idea: separate three jobs that corrupt each other when one mind does them at once —
**gathering facts**, **proposing designs**, and **attacking designs**.

```
Phase 0  scope inline: pin the question, verify current state, inventory evidence
         sources, test live access (read-only)
Phase 1  STUDY  — parallel readers (business docs / target schema / source schema /
         usage data / comparison flow), each returns structured citable findings
Phase 2  DESIGN — same digest to 3 designers with conflicting value systems
         (fidelity-first / consumer-first / minimal-change), blind to each other
Phase 3  VERIFY — adversarial reviewer re-checks primary sources and attacks every
         design: nonexistent fields, broken consumers, unimplemented conventions
Phase 4  synthesize a phased advisory: problems ranked by pain, quick wins first,
         riskiest piece last and severable, plus explicit "what NOT to do, and why"
```

- **Live system over docs:** documented conventions are verified against reality before any
  design may rely on them.
- **Usage data settles arguments:** every number carries the query that produced it; raw
  evidence is saved to disk for audit.
- **Scales down:** without subagents the phases run sequentially solo — the discipline that
  matters is never letting design start before the study is written down.
- Ships `references/workflow-template.md` — a ready-to-adapt Claude Code `Workflow` script
  with the three JSON schemas (findings / design / feasibility).

## crm-archaeology

Use when facing an existing Dynamics 365 / Dataverse org you did not build —
onboarding to a customer's CRM, documenting an undocumented system, or scoping a
migration. The core idea: a live org is unreadable in the browser, but almost
everything in it can be **pulled to disk as plain text** — then it's a normal
legacy-code study.

```
EXTRACT (solution export/unpack + verified Web API queries → fragments/)
   → STUDY (verify static maps against the running app, trace lifecycles)
   → DOCUMENT (assemble one ARCHITECTURE.md, every entry with a Why row)
```

- **Every business entity**, not just custom ones: union of app components,
  sitemap, customized standard tables, and record counts/usage.
- **Both command-bar generations**: classic RibbonDiffXml (incl. the
  Application Ribbons component) and modern `appaction` commands (Power Fx from
  the command component library `.msapp`).
- **Two depths:** quick pass (entity map + automation inventory) or full study.
- **Resumable + drift-aware:** per-step fragments in a git workspace —
  re-export later and `git diff` answers "what changed in the org?".
- Ships `references/extraction-queries.md` (every command/query, verified
  against Microsoft Learn) and `references/architecture-template.md`.

## Prerequisites

- `grill-then-plan` → the **superpowers** plugin (auto-checked).
- `problem-description` → none. Output is a single static HTML file you open in any browser.
- `management-talk` → none.
- `fit-gap-analysis` → none. Verifies against whatever live system you point it at (DB / API / metadata endpoint / running config); no fixed dependency.
- `study-design-verify` → none required. Uses the Claude Code `Workflow`/subagent tools when available, degrades to a sequential solo discipline when not.
- `crm-archaeology` → the **Power Platform CLI** (`pac`) and admin/customizer access to the target environment (prefer a sandbox). The **dataverse** plugin is optional but recommended — its `dv-connect` skill owns auth/setup.
