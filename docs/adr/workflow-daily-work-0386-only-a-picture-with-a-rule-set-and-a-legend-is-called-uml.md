# Only a picture with a rule set and a legend is called UML

```mermaid
flowchart TD
    Q{"The plan's new mode table called the state-machine mode<br/>'a UML state machine diagram'. That pack has no notation rules,<br/>no legend and no checker gate, and this work does not touch it.<br/>What does SKILL.md call it?"}
    Q -->|chosen| A["Its name only: state-machine. SKILL.md says UML for<br/>the sequence mode and for kit pictures, which have rules (ADR 0363),<br/>a legend or caption, and checker gates J and K"]
    Q -->|rejected| B["Keep the label: it promises a notation nobody checked,<br/>the thing ADR 0363 exists to stop"]
    Q -->|rejected| C["Bring the state-machine pack up to UML in this work:<br/>a fourth pack rewrite, outside what was asked"]
```

Found by the Task 6 review. A test now fails if SKILL.md says "UML state machine".
Giving the state-machine pack UML rules (initial and final state, guard syntax, a legend)
is a separate piece of work, not started.

The same review round also corrected one sentence that was wrong about the checker: an id
built as `'m' + n` does not slip past the scene-id pass, it is read as the id `m` and
fails; a template string or a variable is what slips past. SKILL.md and the checker's
comment now say so.
