# The user picks the song from a list before any cut

```mermaid
flowchart TD
    Q{who chooses the song?} -->|chosen| A["the skill lists 5-7 songs that fit the style file,
    each with its shape (where it builds, where it drops)
    and an explicit-lyrics warning, then waits for the
    user's pick before it places a single clip"]
    Q -->|rejected| B["the skill picks from the style file and cuts to the
    export - every cut point is computed from the song's
    beat, so a song the user rejects means re-cutting the
    whole video"]
```

On the first run (2026-11-07) the user rejected the first song after it was cut. Changing
the song meant deleting all 21 clips and cutting them again, because the shot lengths and
the drop point came from the old song's beat. The user then asked for a list first
("ลองลิสมาก่อน") and picked from it. One round of waiting at the start costs less than a
re-cut at the end. Decided by the user on 2026-11-07.
