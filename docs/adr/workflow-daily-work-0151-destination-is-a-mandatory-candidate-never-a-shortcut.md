# A declared destination enters Station 3 as a mandatory candidate, never as a shortcut past the gate

```mermaid
flowchart TD
    Q{"where does a user-declared<br/>destination enter the pipeline?"} -->|chosen| A["optional preflight input — pass 2b<br/>auto-includes the destination's job<br/>families; Station 3 argues the destination<br/>against the four tests ALWAYS, alongside<br/>1-2 comparator candidates; the Station 4<br/>gate is unchanged; the destination is<br/>recorded in growth-state.md and<br/>re-validated every round (ADR 0050)"]
    Q -->|rejected| B["skip Stations 3-4 and backward-chain<br/>the plan — faster, but nothing stress-tests<br/>the destination; round 2's four-test lens is<br/>what surfaced the spoken-English gate"]
    Q -->|rejected| C["no mode — the destination changes<br/>mid-file informally, as round 2 actually<br/>happened; nothing re-validates it and the<br/>artifacts contradict each other"]
```

Round 2 ran destination-first de facto ("Solution Architect, Bangkok, BA
stack") and the skill had no seat for it — the question changed mid-file. The
destination becomes an optional preflight input (pre-filled from the previous
round's `growth-state.md`): it forces its job families into pass 2b's
deep-dive set, must be argued against the four tests in Station 3 next to at
least one comparator, and stands or falls at the Station 4 gate like any
candidate — the user may confirm it against a failing verdict, but the skill
never silently swaps it. Recorded in `growth-state.md` (contract change ADR'd
separately) so every later round re-validates rather than re-derives it.

- Preserves ADR 0045's gate and ADR 0050's full-run rule; extends
  workflow-daily-work-0148/0149's pass structure.
