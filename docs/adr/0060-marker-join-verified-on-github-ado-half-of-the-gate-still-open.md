# ADR 0060 — The marker join is verified on GitHub; the ADO half of the phase-2 gate stays open

- **Status:** Accepted
- **Date:** 2026-08-01
- **Relates to:** [ADR 0059](0059-v1-ships-local-backend-only-tracker-backends-deferred.md) (which set the gate),
  [ADR 0057](0057-chart-is-additive-so-fog-graduation-needs-no-new-subcommand.md),
  [ADR 0058](0058-additive-chart-unions-blocked-by-on-existing-tickets.md)

```mermaid
flowchart TD
    Q{"ADR 0059 gated both tracker backends<br/>on a six-step probe. It has now been run<br/>against GitHub. What does that unlock?"} -->|chosen| SPLIT["split the gate: GitHub is CLEARED<br/>(marker survives every round trip,<br/>native sub-issues + dependencies are GA),<br/>ADO stays gated on the Boards web-UI test"]
    Q -->|rejected| ALL["declare phase 2 open —<br/>the GitHub result says nothing about<br/>ADO's HTML field, where all the risk is"]
    Q -->|rejected| WAIT["keep both gated until ADO is testable —<br/>discards a verified result and leaves the<br/>contract carrying falsified fallbacks"]
```

## Context

ADR 0059 deferred both tracker backends behind a six-step probe of one bet: that a
`<!-- decision-map:key:<key> -->` marker written into an item's body survives round
trips through the tracker. Steps 1–5 are ADO-shaped, step 6 is GitHub.

The probe was run against GitHub on 2026-08-01, in a throwaway **private** repo so
nothing landed in a shared one. `plugins/decision-map/scripts/probe_tracker_github.py`
is the harness; it is committed so the result is reproducible rather than anecdotal.

## Decision

**The gate splits.** GitHub is cleared for phase-2 implementation. ADO stays gated on
step 3 — editing a `System.Description` in the Boards web UI and re-fetching it.

Evidence for clearing GitHub:

- A 122-char body came back **byte-identical** after create → `GET`, and again after a
  close/reopen.
- After a human edited that body **in the web UI**, it came back as exactly the
  original plus what was typed — all three markers intact, no line-ending rewrite, no
  sanitiser. The edit happened to land *inside* a `decision-map:fog` region, which is
  the scenario the design most feared.
- A key containing `--` survives the API verbatim. The format rule stays anyway: the
  local backend rejects such keys at mint time, and the rule exists for rich-text
  editors, which is ADO's problem, not GitHub's.
- Native **sub-issues** (GA 2025-04-09) and native **issue dependencies**
  (GA 2025-08-21) both write and read end to end.

Why ADO cannot ride on that result: GitHub stores issue bodies as literal Markdown,
so an HTML comment is inert text. ADO stores `System.Description` as **HTML**, and
Microsoft documents *nothing* about sanitisation of work-item HTML fields or comment
survival. The two trackers share a marker format, not a storage model, and the whole
reason ADR 0059 deferred was the editor that only ADO has.

## Consequences

- ➕ Phase 2 can start on GitHub against a verified design instead of a hoped-for one.
- ➕ The probe is a committed script, so the ADO half is one command plus one human
  browser edit away whenever an org is reachable — it does not need re-deriving.
- ➖ The contract now describes two trackers at different confidence levels; every
  GitHub row is evidence-backed and every ADO row is documentation-backed at best.
- The probe **falsified three things the contract asserted**, all now corrected: the
  task-list fallback for sub-issues (dead — native REST is GA), the conditional
  `blocked-by: #<n>` body-line fallback (dead — native dependencies are GA), and the
  GitHub `state_reason` rule (wrong — a closed issue can carry `state_reason: null`
  and the enum has grown). A fourth was confirmed by accident: `body` can be JSON
  `null`, seen on two live issues, so every body read must handle it.
- It also surfaced hard limits the contract never stated — **100 sub-issues per
  parent**, so a map cannot exceed 100 tickets; mutations keyed on the issue
  *database id* rather than its number; and an 80-per-minute secondary write limit
  that paces a large `chart`.
- **One gap is now concrete rather than theoretical:** the contract says generated
  regions are tool-owned but never says what happens when a human edits *inside* one.
  The probe's web-UI edit did exactly that, and the next `chart` would overwrite the
  line without warning. This is the same class of bug that took the local backend five
  review rounds to fix by moving to sentinel-delimited regions. Phase 2 must close it
  before writing join code.
