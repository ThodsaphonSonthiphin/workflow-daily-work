# A requirement is one behaviour-binding statement with a minted ID in a per-project register

```mermaid
flowchart TD
    Q{why-this-logic traces code → source today; to trace<br/>requirement → code → test as well, what is 'one requirement'<br/>and where does its ID come from?} -->|chosen| A["one statement that binds behaviour - 'older than 7
    days' is one, 'not yet actioned' another, each
    acceptance-criteria bullet another; the skill mints
    R-001, R-002 … and keeps them in docs/why/requirements.md:
    ID → statement → source locator → rows that implement
    it → tests that cover it; a source that already carries
    an ID (FR-12) keeps it, nothing is re-minted"]
    Q -->|rejected| B["the requirement is the whole ticket or spec
    paragraph, named by its native handle (#151, spec §4 W3)
    - a forward trace then means reading every Why file for
    the handle, and a changed sentence cannot be found
    apart from its neighbours"]
```

Chosen 2026-10-29. The owner asked that `why-this-logic` carry "the requirement trace
ability of a software engineer" - forward and backward, with a matrix. A per-function
answer was rejected for the backward direction in ADR 0261 for the same reason this
rejects a per-ticket requirement: the unit must be the smallest thing that can change on
its own. The ID shape follows `architect-and-verify`'s `N-01` / `C-01` rows, where one ID
sits on the row, the arrow and the test; the forward / backward rule follows
`generating-test-cases` ("every requirement → ≥1 case; every case → real evidence").

The register is one file per project, beside the Why files, so a requirement that several
functions implement is one row with several pointers, not one row per Why file.
