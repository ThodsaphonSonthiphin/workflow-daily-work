# chart-map opens its messages with the Frame line too, naming the briefing point

```mermaid
flowchart TD
    Q{"a ticket with no map yet goes briefing -> chart-map,<br/>which asks the most in one run (13 points, then the<br/>ten-area sweep). Does chart-map get the Frame line as<br/>work-map does (ADR 0393)?"} -->|chosen| A["yes, the same one-line rule. No Decision ticket exists
    yet, so the line names the tracker ticket and AC line,
    the briefing point's letter, the map slug, question N
    of M and the stage - '#196 AC-4 · briefing point C ·
    chart map ado-193 · question 3 of 13 · plan (2/4)'"]
    Q -->|rejected| B["work-map only this round - chart-map runs once per
    Feature, so it is met less often; but on 2026-10-28
    the person ran /wait-what twice inside chart-map for
    the same reason, and the rule is the same line"]
```

Ruled 2026-11-24 by the user (Pon): "a", from two options the agent laid out, in the same
grill-then-plan session as ADRs 0392-0396. The agent recommended A; the cost accepted is a
third skill edited (resolve-the-ticket, work-map, chart-map).

For the line to be writable, resolve-the-ticket hands chart-map each point with its letter
and its locator ("#196 AC-4") on the yes - the same facts it already turns into the
Decision ticket's "Touches" sentence (ADRs 0346, 0395). A chart-map run started directly,
with no briefing behind it, has no letters: the line then carries the map slug, the question
number and the step (destination, frontier, sweep).
