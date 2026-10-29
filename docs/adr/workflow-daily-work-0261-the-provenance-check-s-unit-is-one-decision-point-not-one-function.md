# The provenance check's unit is one decision point, not one function

```mermaid
flowchart TD
    Q{the user asks "is this logic / value correct?" -<br/>what does the skill trace: the whole function,<br/>or each decision inside it?} -->|chosen| A["one row per decision point - every condition,
    every literal, every default - each with its own
    why, its own source and its own verdict; the thing
    pointed at may be code, a ticket, a document or
    pasted text, not only a function"]
    Q -->|rejected| B["one answer per function - 'this comes from
    ticket #X' - hides that the branches and the
    numbers inside it have different origins, and
    some have none"]
```

The user's own example on 2026-10-29 decided this. They pointed not at a function but at an
Azure DevOps story (`Elevate` #151) and asked why its OData filter says
`(mgw_loggingstatus eq 914120001 or mgw_loggingstatus eq 914120003)`, naming a document
folder as the source. One expression, and already two separate questions with two separate
answers: *why does the condition exist at all* (the spec's Workflow 3 lists two filter terms
and never mentions `mgw_loggingstatus` - no source), and *what do the two numbers mean* (the
spec defines the field by label only - `Creating`, `Created`, `Partial`, `Failed` - and the
number-to-label map lives nowhere in the documents). A per-function answer would have
reported one ticket and missed both.

So the skill (name pending) takes code, a ticket, a document or pasted text, breaks the part
the user points at into decision points, and traces each one on its own row.
