# A pass older than the last change is stale and keeps the ticket not ready

```mermaid
flowchart TD
    Q{"a test passed, and after that the thing it tested<br/>changed. What is the old pass worth at the check?"} -->|chosen| A["STALE. The skill compares each pass's date with the
    last change it can see - a git commit on the file, the
    modified date written in the runbook or a snapshot,
    the ticket's revision. A stale row keeps the ticket
    NOT READY until it is tested again, or the user says
    the change does not touch that row (marked told)"]
    Q -->|rejected| B["a warning on a row that still passes - a warning
    beside READY is read as READY; this is the case that
    reopens tickets"]
    Q -->|rejected| C["no date comparison - a written pass would then
    certify a thing that no longer exists in that form"]
```

Ruled 2026-11-16 by the user (Pon), taking the recommended option. The row shows both dates
(`passed 2026-11-10; changed 2026-11-12`) so the person can judge it. A pass with no date
cannot be compared: it is shown as `pass (no date)` and counted in the verdict line with the
told rows. The skill compares against what the documents and git already show; a change date
that only the live system holds is read by one read-only query, asked for per query and per
run, in `why-this-logic`'s shape (ADR 0275) - that part is the agent's reading of "the last
change it can see", not the user's words.

Amended by ADR 0331: the ticket counts as a change only through an edit to its requirement text.
