# The live-read ask is per query: a yes is never carried to another row or another run

```mermaid
flowchart TD
    Q{ADR 0263 says 'ask once per run'; SKILL.md also says<br/>'a yes on row 2 is not a yes on row 5' - which is it?} -->|chosen| A["per query: one ask for each read-only request on
    each open row; the yes covers exactly that query;
    nothing is carried to another row or to the next run"]
    Q -->|rejected| B["once per run, literally - invites one batched ask
    that covers every open row, which is a standing
    permission by another name"]
```

Ruled 2026-10-29 at the final whole-branch review (deferred minor from the Task 1 review).
ADR 0263's "once per run" meant "not a standing permission"; the wording let an agent read
it as "one ask covers the run". The wording in `SKILL.md` phase 3 and its rules list is now
"once per query", which is what ADR 0263 intended.
