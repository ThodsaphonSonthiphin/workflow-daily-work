# chart-map runs a frontier sweep after the human-led grill, and every swept area ends as ticket, fog, out of scope, or a recorded none

```mermaid
flowchart TD
    Q{Step 2 says "fan out across the whole<br/>space" but never names the space —<br/>how does a chart stop missing security,<br/>RBAC, rollback, deploy limits?} -->|chosen| A["a fixed frontier-sweep list (a reference
    file of ~10 software-engineering areas) that
    chart-map walks AFTER the human-led pass:
    ask in one turn which unswept areas matter,
    dig one at a time only into those the user
    picks; every area ends as ticket / fog /
    out of scope / NONE, and none is written on
    the map so the next session can tell swept
    from never asked; the no-fog-no-map rule
    runs only after the sweep"]
    Q -->|rejected| B["a questionnaire the agent asks
    area by area from the start — ten turns
    before the user's own concerns get a
    hearing, and the HITL guard already says
    the human leads"]
    Q -->|rejected| C["leave breadth to the grill — the
    space is whatever the human happens to
    mention, which is exactly the gap observed
    on live maps"]
    Q -->|rejected| D["put the list in sp-grill-with-doc —
    that skill grills one design deep; breadth
    is chart-map's job (work-map SKILL.md:331),
    and the list must feed the map's own
    ticket / fog / scope verdicts"]
```

Live maps charted for software efforts were observed to carry no ticket, fog line
or out-of-scope line about security, authorization, backup and rollback, or
deployment limits — not because those were decided, but because chart-map's
breadth-first Step 2 names no areas to fan out across, so the frontier is only as
wide as what the human happens to raise. chart-map therefore gains a **frontier
sweep**: a coverage pass over a fixed reference list of areas, run *after* the
human-led grill so the user's own concerns are heard first, asked in the user's
terms as one batched question ("these areas are untouched — which matter?") and
then one area at a time only where the user picks. Each swept area must end in one
of four verdicts — the three Step 2 already has, plus **none**, recorded on the map
— because a map that cannot distinguish "swept and empty" from "never asked" would
reproduce the original gap for every later session. The "no fog anywhere → no map
needed" stop moves to after the sweep, since a grill that surfaced no fog before
sweeping has not yet looked. The list's contents and the shape of the none record
are separate decisions (ADR 0223 and following).
