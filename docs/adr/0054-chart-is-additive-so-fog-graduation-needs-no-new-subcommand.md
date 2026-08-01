# ADR 0054 — `chart` is additive, so fog graduation needs no new subcommand

- **Status:** Accepted
- **Date:** 2026-08-01

```mermaid
flowchart TD
    Q{"how does a session add tickets<br/>to an existing map when<br/>fog graduates?"} -->|chosen| ADD["`chart` is additive by default —<br/>creates only tickets whose key is absent,<br/>never touches existing ones; `--force`<br/>stays the explicit full-rewrite escape"]
    Q -->|rejected| SUB["an 8th `add-tickets` subcommand —<br/>clearer name, but a second create path<br/>to implement, test and gate in all three<br/>backends for the same act"]
    Q -->|rejected| V2["defer graduation to v2 —<br/>guts the fog-of-war loop that is<br/>the whole point of a map"]
```

## Context

The ops contract (ADR 0037) shipped seven subcommands: `chart`, `read`, `frontier`,
`claim`, `resolve`, `comment`, `block`. None of them adds a ticket to a map that
already exists — yet the work-the-map flow's final step *graduates fog into fresh
tickets*, and ADR 0039 already classes "every ticket created mid-map when fog
graduates" as a **create-class write**, the same class as charting.

The hole surfaced during implementation. The local backend's first review found that
re-running `chart` silently destroyed recorded decisions; the fix made `chart` refuse
by default with a `--force` full rewrite. That closed the data-loss bug and exposed
the real gap: the only way to add one ticket was to wipe the map.

## Decision

`chart` is **additive by default** on an existing map: it creates only the tickets
whose `key` is not already present, leaves every existing ticket untouched, and
merges `notYetSpecified` / `outOfScope` lines into the map body without disturbing
the Decisions-so-far index. `--force` remains the explicit, dry-run-announced full
rewrite. The dry run reports per item which of `create` / `skip (exists)` /
`OVERWRITE` would happen, so the ADR 0039 approval gate stays truthful.

One create path serves both acts, exactly as ADR 0039 already grouped them — no
eighth subcommand, no second gate to keep in sync across three backends.

## Consequences

- ➕ Fog graduation is just `chart` with the new tickets in the input; the work-map
  flow needs no mechanism the contract lacks.
- ➕ `chart` becomes safely idempotent — re-running the same input is a no-op, which
  also makes a partially-failed chart resumable.
- ➖ "Chart" now names two acts (initial and incremental); the contract must say so
  plainly, or a reader expects create-only semantics.
- ➖ Each backend must match tickets by `key` — cheap locally (filenames), an extra
  title/tag lookup on ADO and GitHub, where the key lives in the item body.
- Supersedes the refuse-by-default half of the local backend's re-chart policy;
  the `--force` rewrite and its dry-run honesty survive unchanged.
