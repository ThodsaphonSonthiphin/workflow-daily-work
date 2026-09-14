# Maps charted before the sweep are swept by an additive re-chart, and lint flags a map that carries no sweep record

```mermaid
flowchart TD
    Q{maps charted before ADR 0222 exist —<br/>how does an old map get swept, and how<br/>does anyone learn it never was?} -->|chosen| A["B+C: the user re-runs chart-map on the
    existing slug; chart-map skips the destination
    and frontier grill that already exist and runs
    only the sweep, writing through the additive
    chart gate (ADR 0057); lint gains a warning,
    map-never-swept, that fires while a map carries
    no sweep record, so every work-map session
    reports it until the re-chart happens"]
    Q -->|rejected| B["A: work-map runs the sweep itself on first
    load of an unswept map — breadth is chart-map's
    job and already done (work-map SKILL.md:331);
    ADR 0212's one-question precedent is a narrow
    exception, not a licence to fan out"]
    Q -->|rejected| C["B alone: re-chart with no signal — the map
    stays silent about what it never asked, which is
    the very defect ADR 0222 exists to remove"]
    Q -->|rejected| D["nothing: the sweep applies to new maps only —
    every live map keeps the gap"]
```

The sweep of ADR 0222 lands in chart-map, but the maps that motivated it were
charted before it existed and will be worked for many more sessions. Breadth stays
chart-map's responsibility, so an old map is swept by running chart-map again on
the existing map: `chart` is additive (ADR 0057), so the run adds only what the
sweep finds — new tickets, fog lines, out-of-scope lines and the none records —
and touches nothing already there. What makes anyone do that is `lint`: a
`map-never-swept` warning fires while the map carries no sweep record, and work-map
already reports lint findings at load and at stop, so the gap is visible every
session until it is closed. ADR 0212 rejected a lint rule for empty milestones
because every fresh map would lint dirty; this rule does not have that property —
a map charted after ADR 0222 carries its sweep record from the first `--real`, so
only pre-sweep maps fire. Known cost: a pre-sweep map whose work is all closed also
fires; whether the rule is narrowed to maps with open work is left to the record's
shape decision, since the rule can only be as precise as the record it reads.
