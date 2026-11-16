# The check is appended to the ticket's runbook, not kept in a file of its own

```mermaid
flowchart TD
    Q{"where does the skill keep the check table and<br/>its verdict?"} -->|chosen| A["in the ticket's own runbook: a 'Resolve check'
    section after the Outcome log, one dated block per
    check, newest last. A later run reads the last block
    first and re-checks only rows that were not PASS or
    that became stale"]
    Q -->|rejected| B["one file per ticket, docs/resolve/<id>.md -
    recommended; the user chose the runbook: one document
    per ticket already holds the baseline, the steps and
    the results, and a second file would split them"]
    Q -->|rejected| C["chat only - every run starts from zero and nothing
    shows that a check was ever made"]
```

Ruled 2026-11-16 by the user (Pon): "Add it to the runbook". The cost named when the option
was offered is real and is handled by a rule, not ignored: the skill appends only - it never
edits a line above its own section - and it never reads its own earlier 'Resolve check'
blocks as proof of a pass; a row's proof is always the test result it points at. The section
is a table inside an existing runbook, so the document's own overview diagram stands and no
new diagram is added.
