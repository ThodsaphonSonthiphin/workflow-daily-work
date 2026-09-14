# The handoff lives in guide-and-verify only — debug-mantra is not edited

```mermaid
flowchart TD
    Q{where does the guide-and-verify → debug-mantra<br/>handoff text live?} -->|chosen| A["in guide-and-verify alone: the freeze line,
    the mapping of what it already has onto the
    four steps, and the return path — debug-mantra's
    SKILL.md is not touched, exactly as ADR 0011 left
    it when grill-then-plan gained its guard"]
    Q -->|rejected| B["also a 'when entered from guide-and-verify'
    note in debug-mantra's prose (recital and diagram
    untouched) — a second place to keep in step, and
    every future caller would want its own note"]
    Q -->|rejected| C["a fifth step or a diagram branch in
    debug-mantra — the recital and the terminal
    diagram are emitted verbatim (ADR 0010); a
    conditional caller does not belong in fixed text"]
```

Ruled by the owner 2026-09-14: *we will not modify debug-mantra.* `debug-mantra` is the
callee; every caller that hands off to it — `grill-then-plan` under ADR 0011, now
`guide-and-verify` under ADR 0214 — carries its own entry conditions in its own SKILL.md, and
says there what it already has for each of the four steps so the callee is not asked for a
repro it was just given. The mantra and the process diagram stay fixed text, and the prose
around them stays caller-agnostic; the alternative is one note per caller in a file whose
whole value is that it reads the same in every session.
