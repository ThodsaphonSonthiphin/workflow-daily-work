# A first run asks once, only what the user left open

```mermaid
flowchart TD
    Q{no style file yet: what does the skill ask?} -->|chosen| A["one round, only the open ones of: frame shape,
    text or no text, kind of music, rules for who is
    shown and how, target length - then write the
    style file"]
    Q -->|rejected| B["every question every time - the user has often
    said some of it already; asking again reads as not
    listening and costs a round"]
    Q -->|rejected| C["no questions, defaults only - the first run of
    this skill produced the wrong shape, text the user
    did not want, and a rejected song"]
```

It follows ADR 0260: a start question the user has already answered is not asked again.
The five questions are the ones the user's corrections on 2026-11-07 showed were missing:
portrait instead of landscape, text overlays, a song kind, how a person was framed, and
how long a moment should run. Agreed by the user in the recap on 2026-11-07.
