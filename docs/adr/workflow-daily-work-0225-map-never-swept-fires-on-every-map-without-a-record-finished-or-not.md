# `map-never-swept` fires on every map without a sweep record, finished or not

```mermaid
flowchart TD
    Q{should the warning stay quiet on a<br/>pre-sweep map whose work is all closed<br/>and whose fog is empty?} -->|chosen| A["no — the rule reads only the Notes
    region and fires on any map with no
    `sweep` bullet; a map that finished before
    anyone asked about security or rollback may
    have finished falsely, and finding that out
    is the whole point; it clears in one
    re-chart, or by a hand-written sweep bullet
    that records 'reviewed, accepted as-is'"]
    Q -->|rejected| B["fire only while the map has open work —
    open tickets, fog or an empty milestone;
    couples the rule to ticket status and
    milestones, and silences exactly the map
    whose 'done' is least trustworthy"]
```

ADR 0223 left open whether the rule should be narrowed to maps with open work,
because the record could not be read until ADR 0224 fixed its shape. It is not
narrowed. The rule reads the Notes region alone and fires on any map that carries
no `sweep` bullet, whether or not its tickets are all closed and its fog empty. A
pre-sweep map that was declared done without ever being asked about an area is the
map most worth flagging, not least; narrowing would hide it. The cost is one
warning per finished pre-sweep map until it is swept, and the cure is cheap: a
re-chart whose every area comes back none writes the record and clears the
finding, and an owner who has already reviewed a finished map may write the sweep
bullet by hand — `sweep <date>: reviewed, accepted as-is` — which is a legitimate
record, not a workaround.
