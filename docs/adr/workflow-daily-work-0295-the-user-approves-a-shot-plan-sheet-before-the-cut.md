# The user approves a shot plan sheet before the cut

```mermaid
flowchart TD
    Q{besides the song, does the skill stop for<br/>the user before it exports?} -->|chosen| A["yes, once: after the song is picked it shows a shot
    plan sheet - one frame per planned shot, its length,
    and whether it sits in the slow part, on the drop or
    in the fast part - and cuts only after the user's OK"]
    Q -->|rejected| B["no: cut, check against the style file, export, and
    take corrections from the finished video - every
    correction then costs a re-cut and a re-export"]
```

On the first run (2026-11-07) nearly every correction the user made after export could be
seen in a still frame: a person framed against the style file's rules, a moment out of
focus, a moment the user wanted longer. A sheet of one frame per shot shows all three
before a clip is placed, so they are fixed in the plan instead of in a re-cut. A still
cannot show how the cut feels against the music; that is still judged from the exported
video. Decided by the user on 2026-11-07.
