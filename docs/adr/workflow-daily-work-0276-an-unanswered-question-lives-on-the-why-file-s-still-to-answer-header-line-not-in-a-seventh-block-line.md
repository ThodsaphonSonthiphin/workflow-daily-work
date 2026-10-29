# An unanswered question lives on the Why file's "Still to answer" header line, not in a seventh block line

```mermaid
flowchart TD
    Q{a second 'I don't know' closes the run with the question<br/>'written into the Why file' - where, when every block has<br/>exactly six lines?} -->|chosen| A["a header line - '- **Still to answer:** row N — <the
    question>' - beside Thing / Traced / Sources searched;
    the six-line block is untouched and the next run sees
    the open question before any row"]
    Q -->|rejected| B["on the row's To-close-it-yourself line - that line is
    about closing the row's SOURCE, not about the user's
    understanding; the two would be confused"]
    Q -->|rejected| C["a seventh line in the block - breaks the
    learn-the-shape-once rule and eval case 0's six-label
    assertion"]
```

Ruled 2026-10-29 at the final whole-branch review (deferred minor from the Task 1 review,
re-placed by the final reviewer). ADR 0267 says the question is written into the file; ADR
0268 fixes the block at six lines. The header is the only place that satisfies both.
