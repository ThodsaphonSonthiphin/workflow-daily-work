# The sequence pack goes to one column below 1340px

```mermaid
flowchart TD
    Q{"ADR 0379 put the switch from two columns to one at 1300px,<br/>from the diagram's 740px minimum width. It left out the wrap's<br/>padding and border (26px) and the page scrollbar (15px):<br/>at 1301px the diagram box had a 9px sideways scrollbar.<br/>Where is the switch?"}
    Q -->|chosen| A["At 1340px. Two columns fit from 1320px without<br/>a page scrollbar and from about 1335px with one"]
    Q -->|rejected| B["Keep 1300px and lower the diagram's minimum to 714px:<br/>the 740px minimum is what keeps 13-unit labels readable"]
    Q -->|rejected| C["Leave it: a scrollbar inside the diagram on every<br/>window between 1301 and 1335px wide"]
```

Found by the Task 5 review, measured at 1301px: column 756.75px, `.seq-wrap` client width
755, scroll width 764. Measured after the change: one column at 1340px and below, two
columns at 1341px with no sideways scroll in the diagram box (scroll width equals client
width at 1341, 1360 and 1500px). This replaces the number 1300 in ADR 0379; the rest of
ADR 0379 stands.
