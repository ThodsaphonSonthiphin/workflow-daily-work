# The register lives beside the Why files in the traced project, and is never written to a tracker

```mermaid
flowchart TD
    Q{where does the traceability live?} -->|chosen| A["docs/why/requirements.md in the project being traced,
    beside its Why files - one file per project, committed
    with the code; the Why files point at it (Source: cited
    R-003) and it points back (implemented at: row 2)"]
    Q -->|rejected| B["a separate folder (docs/traceability/) - the matrix
    and the rows it cites live in two places a reader
    must know"]
    Q -->|rejected| C["written back into the ticket tracker - the skill
    never writes to a live system (ADR 0263), and a
    tracker field cannot be diffed with the code"]
```

Chosen 2026-10-29. The register is read column-wise as the traceability matrix: an empty
*tested by* cell is `generating-test-cases`' work, an empty *implemented at* cell is a gap.
Both directions resolve inside one folder of one repo, which is what lets a new developer
open `docs/why/` and find everything.
