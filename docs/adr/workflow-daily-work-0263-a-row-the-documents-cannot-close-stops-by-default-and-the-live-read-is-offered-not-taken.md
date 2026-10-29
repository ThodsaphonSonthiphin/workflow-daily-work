# A row the documents cannot close stops by default, and the live read is offered, not taken

```mermaid
flowchart TD
    Q{a decision point's value cannot be checked from the<br/>documents the user gave - the map lives only in the<br/>live system; what does the skill do?} -->|chosen| A["stop: mark the row 'cannot check from the document',
    show the exact read-only query that would close it,
    and ASK the user whether the skill may run that query
    itself; yes -> run it read-only, mark the value
    'measured'; no -> the row stays open with the query"]
    Q -->|rejected| B["always read the live system when access exists -
    the user wants to decide, per run, whether an agent
    touches a live Organization at all, even read-only"]
    Q -->|rejected| C["never read the live system - in Dataverse work the
    option-set numbers exist nowhere else, so the most
    important row would stay open every run"]
```

> **Amended 2026-10-29 by ADRs 0272 and 0275:** a query output the user runs and pastes is *measured* (run by who, date), not *told*; and "once per run" means once per query - a yes is never carried to another row or another run.

Decided 2026-10-29 on the `Elevate` #151 example: the spec names the `mgw_loggingstatus`
values (`Creating`, `Created`, `Partial`, `Failed`) and the story uses numbers
(`914120001`, `914120003`); only the live Dataverse holds the map between them. The user
chose "A by default, and ask the user whether to let the AI do B".

So the skill never opens a live system on its own. A row the documents cannot close is
reported as such, with the one read-only command that would close it, and one question:
run it? On yes, the skill runs exactly that query, read-only, and marks the result
*measured*; a value a person states instead is marked *told*. On no, the row stays open and
the command stays in the report for the user to run later. The ask is per run, not a
standing permission.
