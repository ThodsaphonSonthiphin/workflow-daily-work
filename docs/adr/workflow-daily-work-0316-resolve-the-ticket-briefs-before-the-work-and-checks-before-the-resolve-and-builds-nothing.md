# resolve-the-ticket briefs before the work and checks before the resolve, and builds nothing

> **Amended 2026-11-18 by ADR 0339.** The skill still builds nothing itself, but it no longer "never starts the skill it names": it offers the skill and loads it on the person's yes. It now has four stages, not two moments (ADR 0337).

```mermaid
flowchart TD
    Q{"the user asked for a skill named Resolve the Ticket:<br/>read the ticket, its parent and its children; read the<br/>runbook and related files; check the Acceptance Criteria<br/>and the logic - do the tests pass?<br/>What is the skill's job, and when is it run?"} -->|chosen| A["two moments, one skill: a BRIEFING before the work
    starts (ticket, parent, children, runbook, files to
    open) and a CHECK before the ticket is set to
    Resolved (every AC line and logic rule against a
    test, then READY or NOT READY)"]
    Q -->|rejected| B["do the whole ticket - read, build, test, resolve.
    None of the three steps the user wrote builds
    anything, and a skill that builds and then judges
    its own build is not a check"]
    Q -->|rejected| C["the check alone - recommended first; the user
    added the briefing: the same reading serves both
    moments, so one skill carries both"]
    Q -->|rejected| D["the briefing alone - nothing then stands between
    'I think it is done' and the State change"]
```

Ruled 2026-11-16 by the user (Pon). Offered three readings of "resolve" - A check before
resolving, B do the whole ticket, C brief me before I start - the user first took A, then
said "let go with c and a". The skill therefore has two moments and never builds or fixes:
the work between the briefing and the check belongs to the other skills of the arc. The
stake was shown with a real case from the user's project: #154 was Resolved and reopened on
2026-11-16 because a rule ("I don't agree" must not be read as consent) had no passing test
at the moment the State changed.
