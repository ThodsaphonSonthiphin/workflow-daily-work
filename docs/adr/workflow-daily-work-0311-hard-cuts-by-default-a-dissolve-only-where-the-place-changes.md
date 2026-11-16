# Hard cuts by default, a dissolve only where the place changes

```mermaid
flowchart TD
    Q{where does the cut use a transition?} -->|chosen| A["a hard cut on the drop and between all fast cuts;
    a short dissolve only where the day changes place
    in the slow part; a fade at the end"]
    Q -->|rejected| B["a transition on every cut - it blurs the beat and
    makes the drop land soft"]
```

The first run (2026-11-07) showed that a transition on a fast cut hides the beat the cut was
placed on, and a dissolve into the drop takes the hit away. A dissolve is kept for one job:
telling the viewer the day has moved to a new place, which only happens in the slow part.
The video ends on a fade so it does not stop on a cut. Decided in the spec (§12-d) and
approved by the user on 2026-11-07.
