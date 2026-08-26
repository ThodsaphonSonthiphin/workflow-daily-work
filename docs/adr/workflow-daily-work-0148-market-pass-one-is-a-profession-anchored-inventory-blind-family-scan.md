# MARKET runs two passes; pass one is a profession-anchored, inventory-blind job-family scan

```mermaid
flowchart TD
    Q{"what anchors MARKET's<br/>first look at the rings?"} -->|chosen| P["two passes — pass 2a scans job<br/>families per ring anchored on the<br/>user's coarsest profession (asked once<br/>in preflight, carried in growth-state),<br/>capped ~8–10 families/ring, and is<br/>FORBIDDEN from using Station 1 output;<br/>pass 2b deep-dives after it"]
    Q -->|rejected| B["anchor on the board's own IT/software<br/>category — boards cut categories<br/>differently and some don't expose<br/>them to automated fetch"]
    Q -->|rejected| K["single pass with wider keywords —<br/>no bright line saying where inventory<br/>terms may not reach, so the streetlight<br/>bias creeps back"]
    Q -->|rejected| S["status quo — survey scoped by<br/>Station 1's inventory; round 1 proved<br/>it blind: the architect job family was<br/>never counted, and the decisive gate<br/>(spoken English) was invisible"]
```

Round 1 of `career-growth` surveyed only keywords grown from the inventory and
missed the job family that round 2 showed mattered most (Business Applications
architect, Ring 3) along with its real gate (client-facing spoken English) —
the streetlight effect was structural, not an execution error. Station 2 now
runs two passes: **pass 2a** enumerates the job families per ring anchored
only on the user's coarsest profession, reads what each family gates on, and
may not consume Station 1's output; **pass 2b** is the scoped deep-dive
(scope settled by a subsequent ADR). The families cap keeps MARKET a
single-session stage (ADR 0047's constraint) — when the cap truncates, the
dropped families are named in `market-report.md`, never silently.

- Amends the Station 2 internals of ADR 0045/0048; ADR 0047's ring set and
  single-session bound are unchanged.
- New preflight input: the coarsest profession, asked once and carried in
  `growth-state.md` (contract change ADR'd separately).
