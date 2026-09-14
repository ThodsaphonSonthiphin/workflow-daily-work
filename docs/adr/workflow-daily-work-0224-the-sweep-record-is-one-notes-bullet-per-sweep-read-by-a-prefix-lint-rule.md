# The sweep record is one Notes bullet per sweep, and lint reads it by prefix

```mermaid
flowchart TD
    Q{how is "this map was swept, and these<br/>areas came back empty" written so both a<br/>reader and lint can see it?} -->|chosen| A["one bullet in the existing Notes region
    per sweep run, opening with the literal
    prefix `sweep <date>:` and listing every area
    under its verdict — none / ticket / fog /
    out of scope; chart writes it as an ordinary
    notes line (ADR 0101, both backends), and
    map-never-swept fires when no Notes bullet
    carries the prefix — an exact-prefix match,
    not a word-overlap heuristic"]
    Q -->|rejected| B["a new tool-owned `## Sweep` region with
    its own markers and a `sweep` field in
    map_input — more precise, but a contract
    change plus chart, union, read and lint work
    on both backends, to record the same fact"]
    Q -->|rejected| C["lines in the fog region — work-map would
    try to graduate them, and a recorded none is
    the opposite of fog"]
    Q -->|rejected| D["one Notes bullet per area — ten lines
    per sweep on a region that ADR 0101 shrank
    because it had become a wall"]
```

ADR 0223's lint rule can only be as precise as the record it reads, so the
record's shape is fixed here. The Notes region already exists, is already a
union-merged list (ADR 0101) and is already written by `chart` on both backends,
so the sweep record is a single Notes bullet per sweep run — `sweep 2026-09-14:
none — performance, operations; ticket — rollback-plan; fog — reliability; out of
scope — cost` — carrying every area under the verdict it received. Only the
`none` entries are new information (tickets, fog and scope lines already stand on
the map), but every area is listed so that a map on which every area became a
ticket still carries the record. `lint_findings` is one shared function over the
map text, so `map-never-swept` is implemented once: it fires when no bullet in the
Notes region opens with the `sweep` prefix. That is an exact match, deliberately
unlike the word-overlap heuristic of `fog-line-graduated`, so it cannot cry wolf;
its one false positive — a hand edit that deletes the prefix — is a genuinely lost
record and should fire.
