# The briefing's open points are sorted by what they do to the work

```mermaid
flowchart TD
    Q{"the briefing ends with open points. A real one had<br/>13, as one flat list of paragraphs. How are they<br/>shown so the person knows what to do first?"} -->|chosen| A["four groups in a fixed order - fix before the work
    starts; decide while designing; rules to keep; touches
    no task - each point lettered, with what it touches,
    who must answer and what happens if it is not fixed.
    Then a small map of what depends on what, then a
    suggested order read off the map"]
    Q -->|rejected| B["the flat list, as first shipped - every point looks
    equally urgent; the person has to work out alone which
    task each one stops and who to ask"]
    Q -->|rejected| C["one section per ticket, its points under it - a
    point that touches three tickets is printed three
    times, and the order between tickets is still hidden"]
    Q -->|rejected| D["drop the points that touch no task - 'swept and
    harmless' then looks the same as 'never noticed'; they
    stay, in the last group, said in words"]
```

Ruled 2026-11-18 by the user (Pon). A briefing on Feature #193 and its stories #194-#197
returned 13 open points as paragraphs; the user said "open point มันอ่านยากอ่ะ" and asked to
see the effect on each task, which points affect nothing, what to fix first, and what
depends on what. The agent re-cut those 13 points into the four groups, a dependency map and
an order; the user approved that shape ("ok you can modify skill"). The briefing stays
read-only and builds nothing (ADR 0316): the order is a suggestion, and a person who must
answer is named only when a file names them - otherwise `not named`.
