# A ticket comment or an attached image that states a requirement mints an ID

```mermaid
flowchart TD
    Q{which parts of a ticket are 'a document statement' for<br/>ADR 0280 - the description and acceptance criteria only?} -->|chosen| A["any part that states a requirement: the description,
    an acceptance criterion, a comment, an attached image
    read through read-picture - with a locator that names the
    part: #151/AC-2, #151 comment 3, #151 image <name>"]
    Q -->|rejected| B["description and acceptance criteria only - ticket-trace's
    own motivating case is a requirement that lived only in
    an annotated screenshot; it would close the row as cited
    and mint nothing"]
```

Ruled 2026-10-29 at the Task 2 review (Minor M6), promoted to an ADR by the whole-plan
review on 2026-10-30. Consistent with phase 2 order 2 ("a requirement is often only an
annotated screenshot") and with the locator-form rule of ADR 0278 as amended.
