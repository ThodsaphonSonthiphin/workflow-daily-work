# ADR 0001 — Store time estimates as hours on a child Task per work item

- **Status:** Accepted
- **Date:** 2026-06-02

## Context

The workflow must attach a **time estimate** to each work item it creates, and the user wants
literal **time (hours)**, estimated **in detail**, **suggested by the tool and confirmed by the
user** at creation time.

Field reality on the target process (Azure DevOps **Agile**), confirmed by querying each work
item type's fields:

| Type | Original Estimate (hours) | Story Points | Effort |
|---|---|---|---|
| Bug | ✅ | ✅ | — |
| **User Story** | ❌ **none** | ✅ | — |
| Task | ✅ | — | — |
| Feature / Epic | — | — | ✅ |

So a **User Story cannot hold an hour estimate** — it only has Story Points. A typical backlog
batch mixes Bugs and User Stories.

We also sampled completed GlassHull items: **no historical estimate data exists** (Original
Estimate, Completed Work, Story Points, and Effort were all empty). Estimates therefore cannot be
calibrated from past actuals.

## Decision

For every leaf work item (Bug, User Story) the workflow creates **exactly one child Task** that
carries the hour estimate:

- `Microsoft.VSTS.Scheduling.OriginalEstimate` = `RemainingWork` = the estimated hours.
- The **detailed breakdown** (each step + hours, then the total) is stored as HTML in the child
  Task's `System.Description`.
- Hierarchy: `Feature → Bug/User Story → Task`.

Estimates are produced by Claude using **work-kind anchors** (rename / disambiguation / missing
field / structural) adjusted for complexity, **presented to the user as a table for
confirmation/adjustment** before anything is created. Items over ~16h are flagged to split.

(Chosen options in the design discussion: **C1** — child Task under every item; **D1** —
breakdown lives in the Task description, one Task per item.)

## Consequences

- ➕ Hours live where ADO actually allows them (Tasks), **uniformly across all item types** →
  consistent roll-up, capacity, and burndown.
- ➕ The detailed breakdown is captured without exploding the item count.
- ➕ Estimates are **human-confirmed**, never silently auto-applied.
- ➖ Roughly **2× the work items** (each Bug/Story gains a child Task), and `create-backlog.cs`
  must create a **3-level** hierarchy.
- ➖ Anchors are heuristic (no history to calibrate against) and will need periodic tuning as the
  team logs real `CompletedWork`.

## Alternatives considered

- **Story Points on the Bug/Story directly** — rejected: not literal time, which the user
  explicitly wanted.
- **C2: Original Estimate on the Bug directly + a child Task only for User Stories** — rejected:
  the estimate would live in two different places (on Bugs vs on Stories' child Tasks), so hours
  can't be rolled up uniformly.
- **D2: one child Task per breakdown step** — rejected: item explosion (8 items → 30+ Tasks).
- **Calibrate estimates from team history** — rejected: no historical hour data exists.
