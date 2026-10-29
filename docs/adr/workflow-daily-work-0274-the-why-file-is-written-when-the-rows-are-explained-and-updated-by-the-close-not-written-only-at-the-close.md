# The Why file is written when the rows are explained, and updated by the close - not written only at the close

```mermaid
flowchart TD
    Q{ADR 0268 writes docs/why/&lt;thing&gt;.md in phase 7, after<br/>the user states the rule - what if they never do?} -->|chosen| A["write the file's skeleton as soon as the rows are
    listed (phase 1: one block per row, every line '—'),
    fill each block as its hit is found (phase 2),
    complete it when the rows are explained (phase 5),
    and let phases 6 and 7 update it (Still to answer,
    the closing offer); a run the user walks out of
    still leaves the file"]
    Q -->|rejected| B["write only in phase 7 - phase 6 has no turn limit,
    so a user who leaves gets nothing, and the next run
    traces from zero: ADR 0268's own rejected alternative"]
```

Ruled 2026-10-29 at the final whole-branch review. `SKILL.md` borrowed `guide-and-verify`'s
"record each hit as it is found" rule and its rationale (a crash or a compaction loses an
unwritten search) - but "its row" was a chat table until phase 7, so the rationale did not
hold. The file is the durable row: its skeleton exists from the moment the rows are listed,
every hit lands in its block, and the explanation completes it. ADR 0268's block shape and
path are unchanged; only *when* is superseded, and that ADR carries the banner.
