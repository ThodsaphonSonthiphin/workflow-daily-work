# The register's overview draws one node per open statement and one count node for the implemented ones

```mermaid
flowchart TD
    Q{the register grows with every run - what does its<br/>Mermaid overview show?} -->|chosen| A["one node per not found and per untested statement, plus
    one node carrying the count of implemented ones; F5 and
    the backward phase-5 refresh redraw the nodes, not only
    the lead-in sentence"]
    Q -->|rejected| B["one node per ID - past about fifteen the diagram stops
    being the thumbnail the diagram convention requires, and
    the template's own example would mislead every run"]
```

Ruled 2026-10-29 at the Task 3 review (Minor 4), promoted to an ADR by the whole-plan
review on 2026-10-30, which found the template's example still drawing an implemented ID
as its own node and no forward step redrawing the nodes - both fixed in the same wave.
