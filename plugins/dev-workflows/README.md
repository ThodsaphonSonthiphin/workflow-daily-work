# dev-workflows

General-purpose **development workflow skills** — the reusable, non-domain-specific
helpers that support day-to-day engineering work. This plugin is a growing collection;
more skills will be added over time.

## Skills

| Skill | What it does |
|---|---|
| `grill-then-plan` | A domain-aware **grilling session**: interviews you one question at a time, challenges your plan against the project glossary, sharpens fuzzy terms, and captures decisions inline (`CONTEXT.md` + ADRs). Writes a design spec, then **hands off to `superpowers:writing-plans`** to produce the implementation plan. |
| `problem-description` | Generate a self-contained **interactive HTML walkthrough** that explains a complex technical problem (DB error, race condition, design issue) with concrete data and manual step-through navigation. Two modes: **diagram** (boxes + data flow) and **tables** (grid state changes). |

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

## Prerequisites

- `grill-then-plan` → the **superpowers** plugin (auto-checked).
- `problem-description` → none. Output is a single static HTML file you open in any browser.
