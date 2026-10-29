# The register is created by the first minted ID, never by an empty open

```mermaid
flowchart TD
    Q{the forward run opens docs/why/requirements.md in F0 -<br/>who creates it when it is absent?} -->|chosen| A["F2, on the first ID it mints (and the backward run's
    phase 2, on the first ID it mints); F0 only opens an
    existing file; a run abandoned before any ID leaves
    nothing behind"]
    Q -->|rejected| B["F0 creates it from the template before the
    requirement text is even known - a run the user walks
    out of at F0 leaves an empty register with example
    nodes, against 'never created otherwise'"]
```

Ruled 2026-10-29 at the Task 2 review (deferred to this ADR by the whole-plan review on
2026-10-30). The spec §6 F0 said "open or create"; the skill now reads "open if it exists;
it is created in F2, by the first ID minted". Same rule for the backward run (ADR 0280).
