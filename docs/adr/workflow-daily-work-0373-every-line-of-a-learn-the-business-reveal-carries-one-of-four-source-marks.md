# Every line of a learn-the-business reveal carries one of four source marks

```mermaid
flowchart TD
    Q{"no ADR and no document gives the<br/>business reason - what does the reveal say?"} -->|chosen| A["every line carries one mark: cited (ADR, file, ticket<br/>with its place), told (who, date), general knowledge<br/>(the trade's rule, not this project's), assumed (the<br/>skill's guess). An assumed line goes into the note<br/>as a question for the client or BA"]
    Q -->|rejected| B["a plausible reason with no mark - the person cannot<br/>tell a document from a guess, and repeats the guess<br/>to the client"]
    Q -->|rejected| C["'no source', and skip the part - the parts with no<br/>document are the ones people understand least"]
```

Ruled 2026-11-21 by the user. The search order before any question: ADRs, specs and
documents in the repo, the ticket with its comments and images, `CONTEXT.md`, commit
messages, tests. *cited* and *told* are `why-this-logic`'s words; *general knowledge* is
`feynman-explain`'s. The person's own answer to a part with no source is written as *told*,
never *cited*, and an answer is never judged wrong against an *assumed* line.
