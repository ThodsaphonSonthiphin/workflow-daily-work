# An over-long gist warns, it does not fail the resolve

```mermaid
flowchart TD
    Q{"how is the one-line<br/>gist rule enforced?"} -->|chosen| A["warn on stderr, still write —<br/>plus sharper SKILL.md wording"]
    Q -->|rejected| B["exit 2 — the answer is not<br/>recorded, breaking the rule that<br/>it lands in the same turn"]
    Q -->|rejected| C["truncate to the limit —<br/>silent data loss on the one<br/>field the map index projects"]
```

`resolve` prints a warning to stderr when the flattened `gist` exceeds the
length a single index line can carry, and writes it anyway. `work-map`'s Step 4
wording is sharpened at the same time — *one sentence, not one paragraph* —
because the current phrasing already says "one line" and every session has
written an essay against it.

Failing the resolve was the tempting option and is wrong: the answer would not be
recorded, and Step 4's rule is that an answer which lives only in the
conversation is lost when the session ends. A tool that discards a hard-won
decision to enforce a formatting rule has its priorities inverted. Truncating is
worse still — the gist is the field the map's "Decisions so far" index projects,
so a silent trim edits the map's only summary of a decision.

This is knowingly the weaker enforcement. It is chosen because the failure it
guards against is a readability regression, not a correctness one, and because
stderr warnings in this codebase already carry real weight — the same channel
names a skipped ticket file and an unapplied divergence.
