# Phase 3 asks one question naming every no-source row, with what was searched

```mermaid
flowchart TD
    Q{several rows are 'no source' after the search; the skill<br/>says 'never a list of questions' - how many asks?} -->|chosen| A["one question that names every no-source row, each
    quoted, with what was searched: 'Rows 1 and 4 -
    nothing in git, the ticket, <folder>, specs, scripts,
    tests. A document or a person for either?' - the
    one-question rule belongs to phase 6"]
    Q -->|rejected| B["one ask per no-source row, one per turn - stretches
    a run of five open rows over five turns before the
    table is even shown"]
    Q -->|rejected| C["ask with no evidence - 'do you have a document for
    row N?' before any table; ADR 0264 says the ask comes
    with what the search found and did not find"]
```

Ruled 2026-10-29 at the final whole-branch review (deferred minor from the Task 1 review,
merged with the final reviewer's note that the phase-3 ask showed no evidence). ADR 0264 is
unchanged in substance - search first, ask only for open rows; this fixes the shape of that
ask and scopes "never a list of questions" to phase 6 (ADR 0267).
