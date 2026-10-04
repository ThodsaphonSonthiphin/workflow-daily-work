# A run that finds its document resumes from it

```mermaid
flowchart TD
    Q{the skill starts, and an architecture document for this<br/>system and environment already exists: what does it do?} -->|chosen| A["it reads the document first, reports the status,
    the open rows, the changes not yet checked and the
    tests owed, and continues from there — nothing is
    asked again"]
    Q -->|rejected| B["it starts a fresh run and asks the three
    questions again — the work spans days, so every
    session after the first would redo what the rows
    already hold, and the second answers can disagree
    with the first"]
```

First stated in the design spec of 2026-10-03 (§4, Phase 0) and approved with it by the
owner the same day. A firewall request takes days, and a test of a connection into the
new system is owed until that system is installed (ADR 0248), so a run is rarely one
session.

The document is the memory. A fact is written into its row when it is taken, which is
why the file is created in the first phase and not at the end; a later session reads the
file, shows what is open, and goes on from the first open row. The results it adds go
into the same rows (ADR 0242).
