# A milestone is first-class structure, not a task-ticket emulation

```mermaid
flowchart TD
    Q{how is a milestone represented?} -->|chosen| A["first-class map structure —
    the contract, both backends and lint
    all know what a milestone is"]
    Q -->|rejected| B["a type:task ticket blockedBy its members —
    zero code change, but adds pseudo-tickets to a map
    the user already finds hard to read, needs FAKE
    dependency edges to order milestone 2 after 1,
    and a 'build the increment' ticket breaks
    'decision-map plans; it does not build'"]
```

A milestone (ADR 0094) could have been emulated today with no contract change: one
`task` ticket per milestone, blocked by its member tickets, surfacing on the
frontier when the members close. Rejected on three grounds. First, the founding
complaint is that the map is hard to read — emulation *adds* tickets that are not
decisions, so it worsens the problem it serves. Second, milestone ordering would
need `milestone-2 blockedBy milestone-1` edges that assert a dependency that does
not exist, and the position diagrams (ADR 0063/0064) would draw that lie on every
member ticket. Third, a ticket whose resolution is "the increment was built" sits
outside the map's charter — decision-map plans and hands off; it does not build.
So milestones enter the data contract as real structure, at the cost of touching
`map_core.py`, both backends, the dry-run plan and lint.
