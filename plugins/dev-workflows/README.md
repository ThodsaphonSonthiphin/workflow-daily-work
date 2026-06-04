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
> If you only want the grilling/docs *without* a plan, use `grill-with-docs` instead.

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

## Prerequisites

- `grill-then-plan` → the **superpowers** plugin (auto-checked).
- `problem-description` → none. Output is a single static HTML file you open in any browser.
- `management-talk` → none.
- `fit-gap-analysis` → none. Verifies against whatever live system you point it at (DB / API / metadata endpoint / running config); no fixed dependency.
