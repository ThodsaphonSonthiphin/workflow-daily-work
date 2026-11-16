# A test proves a row only when its Given, When and Then all match

```mermaid
flowchart TD
    Q{"the check pairs each AC line and logic rule with a<br/>test. How does it decide that the test proves<br/>the row, and how does the person see why?"} -->|chosen| A["the row and the test are each broken into Given
    (the state before), When (the event) and Then (the
    result). All three match: the test proves the row.
    One part differs or is not stated: the row is 'no
    test' and names the part. One reasoning line per row
    is printed under the table. Boundary values are a
    note under the verdict, never a result"]
    Q -->|rejected| B["pair by topic, as the first version did - a test
    about the same feature passed the row; the reasoning
    stayed invisible and a wrong pairing read as pass"]
    Q -->|rejected| C["boundary values decide the verdict too - almost no
    hand-tested ticket covers every edge, so nearly every
    check would read NOT READY and the verdict would be
    ignored"]
    Q -->|rejected| D["a free-text 'why' per row with no fixed parts - it
    cannot be compared row to row, and 'close enough'
    fits any wording"]
```

Ruled 2026-11-16 by the user (Pon), after asking whether the skill lacked a step-by-step way
of thinking and which method software engineers use. Given-When-Then is the behaviour-driven
development form (Specification by Example); the table of rows against tests is the
requirements traceability matrix the skill already had; boundary value analysis is the
note. The motivating case is the one behind the skill: #154 was resolved with a consent
test that passed and reopened because "I don't agree" was read as consent - the test's
*When* was not the rule's *When*. Reading that test as answering a plain "no" is the
agent's illustration, not a measured fact. Adds a step to the order of ADR 0319's check;
a told row gets the same three questions.
