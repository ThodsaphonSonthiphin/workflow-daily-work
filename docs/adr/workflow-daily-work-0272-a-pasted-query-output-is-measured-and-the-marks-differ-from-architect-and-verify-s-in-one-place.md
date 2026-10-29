# A pasted query output is `measured`, and the marks differ from architect-and-verify's in one place

```mermaid
flowchart TD
    Q{the user declines the live read, runs the query<br/>themselves later and pastes the output - what mark?<br/>and are the three marks really architect-and-verify's?} -->|chosen| A["measured: the query (run by <who>, <date>) - the
    output travelled through the user, as guide-and-verify
    already says; a value STATED without the output is
    told; and the glossary says the one difference out
    loud: in architect-and-verify an old document is told,
    here a document or commit is cited and told is only a
    person's word"]
    Q -->|rejected| B["told, because ADR 0263 says 'a value a person
    states is told' - this makes a real measurement look
    like hearsay and gives CONTEXT.md two meanings of told"]
    Q -->|rejected| C["keep claiming the marks are identical to
    architect-and-verify's - a reader who knows one skill
    then misreads the other, the opposite of what
    ADR 0266 wanted"]
```

Ruled 2026-10-29 at the final whole-branch review. ADR 0266, spec §11 and `CONTEXT.md` said
the three marks "are the same three `architect-and-verify` uses". They are not:
`architect-and-verify` marks an old document *told*, and this skill marks a document *cited*.
And the path ADR 0263 leaves open - "the query stays on the row for you to run later" - had no
mark for the output the user brings back. `guide-and-verify` settles that: a pasted result "is
genuine measurement - it just travelled through them".

Corrections land in the same change: a banner on ADR 0266 and on ADR 0263, the `CONTEXT.md`
**Proof mark** entry, spec §11, and one sentence in `SKILL.md` phase 3.
