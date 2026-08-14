---
title: Coexistence - does the superpowers plugin stay enabled alongside the copies?
type: grilling
mode: HITL
status: closed
assignee: coexistence-grill-1420
blocked_by: [harness-skill-shadowing]
gist: Plugin stays enabled; the six review-carrying originals go off via skillOverrides - the other eight skills stay live and the copies' outbound refs keep resolving.
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["coexistence (this ticket)"]
    P0["harness-skill-shadowing"] --> ME
    ME --> C0["arc-rewiring"]
    ME --> C1["copy-granularity"]
    ME --> C2["skill-naming"]
```
<!-- decision-map:graph:end -->

## Question

Do we keep superpowers@claude-plugins-official enabled and accept two copies of brainstorming / writing-plans / the review skills competing for the same triggers, or disable it and take over every skill we depend on (including the ones with no review step)? The answer sets the naming, the copy granularity and how much of the daily arc has to be repointed.

<!-- decision-map:resolution:start -->
## Resolution

Plugin stays enabled; the six review-carrying originals go off via skillOverrides - the other eight skills stay live and the copies' outbound refs keep resolving.

Detail: docs/adr/0069-the-upstream-plugin-stays-enabled-its-review-skills-go-off-per-skill.md

```mermaid
flowchart TD
    S["superpowers plugin<br/>STAYS ENABLED"]
    S --> OFF["the 6 review-carrying skills<br/>skillOverrides: off"]
    S --> LIVE["the other 8 skills<br/>stay live"]
    S --> HOOK["SessionStart hook<br/>still fires"]

    OFF -.->|"displaced by"| COPIES["vendored copies in this repo<br/>review step routed to scrutinize"]

    LIVE --> D1["3 outbound refs INSIDE the copies<br/>keep resolving:<br/>using-git-worktrees, finishing-a-development-branch"]
    LIVE --> D2["3 refs in this marketplace<br/>keep resolving:<br/>systematic-debugging, writing-skills,<br/>finishing-a-development-branch"]
    COPIES --> D1

    HOOK --> GAP["OPEN: the hook still names<br/>superpowers:brainstorming by qualified name.<br/>skillOverrides cannot reach a hook."]

    style OFF fill:#fdd
    style COPIES fill:#dfd
    style GAP fill:#ffd
```

The reasoning, the three rejected positions and the two holes this answer leaves
are in ADR 0069, linked above. It is canonical; this block does not restate it.

## What it graduated onto the map

- `skilloverrides-live-check` (task) — the hook still names
  `superpowers:brainstorming` by qualified name after it is switched off, and the
  exact key form `skillOverrides` expects for a plugin skill was inferred, never
  observed. Blocks `skill-naming`.
- `override-distribution` (grilling) — a plugin cannot ship a settings key, so on
  a machine without those six entries this decision degrades silently into
  "change nothing". Blocks `antigravity-install`.

## One measurement was corrected in session

An in-session figure of **5** references from this marketplace to non-review
superpowers skills is **wrong** — it double-counted the
`.claude/worktrees/decision-map/` checkout. The measured count on `29ff84c`,
tracked files only and excluding `docs/decision-map/`, is **3**, and that is the
figure the ADR carries. The correction did not change the decision.

## Confirmation

Four positions were put to the user as a table, with this one recommended and the
consequence of "change nothing" walked through concretely. The user answered:

> b

<!-- decision-map:resolution:end -->
