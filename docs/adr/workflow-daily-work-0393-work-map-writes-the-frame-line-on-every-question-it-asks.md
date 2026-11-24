# work-map writes the Frame line on every question it asks

```mermaid
flowchart TD
    Q{"the Frame line (ADR 0392) must open every plan-stage<br/>question. work-map is loaded two ways: by<br/>resolve-the-ticket on a yes, and directly from a<br/>conversation. Which skill writes the line?"} -->|chosen| A["work-map, as one rule in its Step 3 (resolve by type):
    every question to the person opens with the Frame line.
    resolve-the-ticket hands it the tracker ticket and the
    AC lines on the yes. ADR 0338 is amended: a one-line
    rule on how a loaded skill talks to the person is not a
    new mode"]
    Q -->|rejected| B["resolve-the-ticket only - it asks work-map for the line
    in its hand-off request, as it asks guide-and-verify to
    name rows (ADR 0340). A direct /work-map call then has
    no line, and two of the three work-map runs of
    2026-11-24 were direct calls (07:45, 10:23)"]
    Q -->|rejected| C["work-map and sp-grill-with-doc both - two skills to
    edit, and sp-grill-with-doc also runs outside a map,
    where there is no ticket to name"]
```

Ruled 2026-11-24 by the user (Pon): "a", from three options the agent laid out, in the same
grill-then-plan session as ADR 0392. The agent recommended A.

Why work-map: it is the skill that claims the Decision ticket, so it knows which ticket a
question serves whoever loaded it. The line is written once, where the question is asked,
and both entry paths get it.

ADR 0338 ("the one entry is built by changing resolve-the-ticket only") is amended, not
reversed: the entry skill is still built in resolve-the-ticket alone, and no loaded skill
gets a new mode. What a loaded skill may now get is a rule on how it speaks to the person.
