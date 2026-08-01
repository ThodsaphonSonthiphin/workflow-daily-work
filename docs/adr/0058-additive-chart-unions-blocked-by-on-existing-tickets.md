# ADR 0058 — additive `chart` unions `blockedBy` on existing tickets

- **Status:** Accepted
- **Date:** 2026-08-01
- **Refines:** [ADR 0057](0057-chart-is-additive-so-fog-graduation-needs-no-new-subcommand.md)

```mermaid
flowchart TD
    Q{"a graduating ticket must block<br/>a ticket that already exists —<br/>who wires the edge?"} -->|chosen| UNION["`chart` unions the edge into the<br/>existing ticket's blocked_by — the<br/>same union semantics ADR 0057 already<br/>applies to fog and out-of-scope"]
    Q -->|rejected| TWOCALL["keep existing tickets byte-identical;<br/>the flow skill calls `block` after<br/>`chart` — preserves the simpler<br/>property but makes graduation a<br/>two-step a caller can forget"]
```

## Context

ADR 0057 made `chart` additive, and Task 3b implemented it with a strict guarantee: every
pre-existing ticket file stays **byte-identical**. Review then established the actual shape
of the resulting hole — narrower than first reported, but real:

- new ticket **blocked by** an existing one → the edge lives on the new file, so it *is* wired;
- new ticket **blocks** an existing one → the edge would have to be written onto the existing
  file, so it was silently dropped.

Fog graduation produces both directions routinely. Worse, the drop was invisible: `frontier()`
then reports a ticket as actionable when a just-created ticket is supposed to block it — the
frontier being precisely what a session trusts to choose its next decision.

## Decision

`chart` **unions** the new edge into an existing ticket's `blockedBy`. The additive guarantee is
restated as **"never removes, never reorders, never overwrites"** rather than "never touches":
an existing ticket may gain a blocking entry and nothing else. This is the same union already
blessed for `notYetSpecified` and `outOfScope` — one rule across every additive merge, rather
than one rule with an exception.

Re-running an identical input remains a no-op, because unioning an edge that is already present
changes nothing.

## Consequences

- ➕ Graduation is one gated call; the frontier can no longer report a blocked ticket as
  actionable because the caller forgot a second step.
- ➕ One mental model — additive means union — for all three backends and for the flow skills.
- ➖ The byte-identity property, established at real cost, weakens to a scoped one. Mitigated:
  the change is append-only to a single list, everything else on the file stays byte-identical,
  and tests must pin exactly that.
- ➖ Every write to an existing ticket must still route through the module's write path so the
  marker-integrity assertion keeps covering it.
- On ADO and GitHub an edge is a link rather than a file mutation, so the byte-identity rationale
  never applied there; this brings the local backend in line with what those backends do anyway.
