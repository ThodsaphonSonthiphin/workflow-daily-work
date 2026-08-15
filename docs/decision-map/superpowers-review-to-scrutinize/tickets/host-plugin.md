---
title: Host plugin - do the copies live in dev-workflows or a new plugin of their own?
type: grilling
mode: HITL
status: closed
assignee: host-plugin-grill-1735
blocked_by: []
gist: The six copies live in plugins/dev-workflows - no sixth plugin: the destination needs Antigravity and its only installer is plugin-local, and ADR 0070's hook must ship beside them.
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["host-plugin (this ticket)"]
    ME --> C0["antigravity-install"]
    ME --> C1["convention-compliance"]
```
<!-- decision-map:graph:end -->

## Question

Do the vendored skills land inside plugins/dev-workflows (one plugin, but six large foreign skills mixed into the daily arc) or in a new plugin such as superpowers-local (its own manifest, marketplace entry, version and one-time enable step)? Decide against the repo's existing plugin boundaries, not just file tidiness.

<!-- decision-map:resolution:start -->
## Resolution

The six copies live in plugins/dev-workflows - no sixth plugin: the destination needs Antigravity and its only installer is plugin-local, and ADR 0070's hook must ship beside them.

Detail: docs/adr/0073-vendored-review-skills-live-inside-dev-workflows-not-a-plugin-of-their-own.md

```mermaid
flowchart TD
    MP["marketplace: still 5 plugins<br/>(version bump only, no new entry)"] --> DW["plugins/dev-workflows/"]
    DW --> SK["skills/ — 25 authored<br/>+ 6 sp-* vendored = 31"]
    DW --> HK["hooks/hooks.json —<br/>ADR 0070's SessionStart hook<br/>ships beside the copies"]
    DW --> AG[".antigravity/install-antigravity.py —<br/>unchanged; it iterates skills/<br/>so it stages the 6 for free"]
    SK --> SC["scrutinize — already here;<br/>every review touchpoint routes<br/>inside one plugin"]
    NP["a 6th plugin"]:::no --> X["displaced: needs a 2nd Antigravity<br/>installer that has never been written<br/>(decision-map still has none)"]:::no
    classDef no stroke-dasharray: 4 3
```

The copies land in `plugins/dev-workflows/skills/`. No sixth plugin; `dev-workflows`
takes a version bump on its existing `marketplace.json` entry.

**What decided it.** The destination requires both harnesses, and Antigravity has
exactly one route in — `plugins/dev-workflows/.antigravity/install-antigravity.py`,
which is plugin-local by construction (`PLUGIN_ROOT` is the parent of its own
`.antigravity/`, shared support hard-coded to `.dev-workflows-shared`) and discovers
skills by iterating `PLUGIN_ROOT/skills`. Inside `dev-workflows` the six are staged with
zero installer changes; in a new plugin they need a second installer — and
`decision-map`, created as the fourth plugin on 2026-07-31, still has no `.antigravity/`
at all. A new plugin has so far meant Claude Code only.

ADR 0070's hook is the second lock: `dev-workflows` is the only plugin here with a
`hooks/` directory, and splitting the hook from the copies lets a colleague enable a
hook that steers at skills they do not have.

**Re-scope during the session.** The grilling opened on a live possibility that
`dev-workflows` was itself being deprecated and folded into a new marketplace, which
would have voided the ticket's whole framing. That was checked before answering — the
repo carries no deprecation record anywhere — and the owner then settled it directly:

> "งั้น dev-workflows ไม่ depecate เก็บไว้ในdev-workflows เลย"

That withdrawal, rather than a deferral, is also why "land it here now and split later"
was rejected instead of kept as a hedge.

**Raised, not settled:** ADR 0072's Step 0 preflight on `sp-writing-plans` can no longer
fail now that `grill-then-plan` ships in the same plugin as its target — it was kept
only because `host-plugin` had not answered. Graduated as its own ticket.

<!-- decision-map:resolution:end -->
