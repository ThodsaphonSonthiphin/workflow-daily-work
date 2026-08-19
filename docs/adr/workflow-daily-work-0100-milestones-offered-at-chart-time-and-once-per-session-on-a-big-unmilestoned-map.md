# Milestones are offered at chart time and once per session on a big unmilestoned map

```mermaid
flowchart TD
    Q{when does the flow invite<br/>the user to declare milestones?} -->|chosen| A["chart-map asks after breadth grilling
    ('what do you want to see first?', skippable) —
    AND work-map offers ONE line when the map has
    no milestones and more than ~5 open tickets"]
    Q -->|rejected| B["chart time only — quiet, but every
    EXISTING map stays flat until the user
    remembers the feature exists"]
    Q -->|rejected| C["work-map nags every session /
    blocks until grouped — a small map is
    fine flat, and a nag trains the user
    to skip everything else in the report"]
```

Two entry moments, both skippable. New maps: chart-map's breadth grilling gains
one closing question — which increment ships first — and writes the answer into
the initial chart's `milestones` input, through the same dry-run gate as
everything else. Existing maps: when work-map loads a map that has **no**
milestones region content and the open-ticket count is large enough that picking
hurts (more than ~5 open), it offers one line — "this map has no milestones; want
to group before picking?" — once per session, never repeated, and declining
changes nothing. The threshold exists because a four-ticket map does not need an
ordering layer, and milestones must never become a toll on small maps.
