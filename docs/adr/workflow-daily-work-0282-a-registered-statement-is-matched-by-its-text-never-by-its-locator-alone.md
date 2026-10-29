# A registered statement is matched by its text, never by its locator alone

```mermaid
flowchart TD
    Q{a run cites spec:145 - the register holds R-003 at spec:145;<br/>when is this the same statement?} -->|chosen| A["when the TEXT matches - at the registered locator, or at
    a new locator in the same section (the line's source gains
    the new locator); a matching locator whose text differs is
    'source changed': the line keeps '<new> (was: <old>)', mints
    nothing, and the run says so before citing it - in either
    direction; the same text in another section is a new
    statement unless the user says it restates the first"]
    Q -->|rejected| B["'same locator, or same text' - two lines inserted
    above spec:145 make a backward run reuse R-003 for
    whatever sentence now sits there, silently; and short
    split clauses ('increments ReminderCount') in another
    workflow take the first workflow's ID"]
```

Ruled 2026-10-30 at the whole-plan review. The previous wording came from the plan and was
copied into `SKILL.md` phase 2, F2 and the register template. The backward run had no
*source changed* path at all - only a later forward run compared text. Now both directions
compare the text first; a locator is a pointer to where the text was last seen, never the
identity. Eval case 6 measures the backward side: a known locator whose text changed.
