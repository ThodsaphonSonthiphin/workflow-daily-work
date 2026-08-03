# The position diagram shows structure only, never status

```mermaid
flowchart TD
    Q{"does a ticket's position<br/>diagram colour its<br/>neighbours by status?"} -->|chosen| A["structure only — refreshed<br/>by chart --real and block,<br/>writing both ends of the edge"]
    Q -->|rejected| B["colour by status — resolve<br/>must rewrite every neighbour's<br/>file to keep it true"]
    Q -->|rejected| C["colour by status, refresh<br/>lazily — a stale 'open' reads<br/>as a blocker that is already gone"]
```

A ticket's position diagram names its blockers, itself and what it unblocks, and
says nothing about whether any of them is open, claimed or closed. Only
`chart --real` and `block` re-render it, because those are the only subcommands
that change a ticket's edges; `resolve` keeps touching exactly one file, as it
does today.

An edge is drawn at both of its ends, so `block(A, B)` rewrites two ticket
files: A gains a parent node and B gains a child node. The dry-run plan must
therefore carry a `merge` entry for each of them, and the assertion in
`test_additive_chart_unions_a_new_edge_into_an_existing_ticket` that every
other ticket stays byte-identical is now pinning something this design
deliberately changes.

Status was rejected twice over. Kept true, it forces a fan-out write — closing
one ticket would rewrite every neighbouring ticket file, turning the cheapest
subcommand into the widest one. Kept lazily, it goes stale in the one direction
that misleads: a diagram still showing a blocker as open, after that blocker
closed, tells the reader they cannot pick the ticket up when they can. That is
the same shape ADR 0061 exists to prevent — an absence or a staleness read as a
fact — and it would be reintroduced by a decoration.

Nothing is lost, because status is already answered authoritatively elsewhere:
`frontier` computes open blockers on every read and `work-map` renders it at
session start. The diagram answers *what is this ticket wired to*; the frontier
answers *can I take it right now*.
