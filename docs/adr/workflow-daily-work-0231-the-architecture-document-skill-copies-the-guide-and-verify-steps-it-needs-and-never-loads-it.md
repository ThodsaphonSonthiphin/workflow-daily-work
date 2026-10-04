# The architecture-document skill copies the guide-and-verify steps it needs — it never loads it, and guide-and-verify is not edited

```mermaid
flowchart TD
    Q{a new skill takes its method from guide-and-verify:<br/>how are the two skills related?} -->|chosen| A["the new skill COPIES the steps it needs into
    its own SKILL.md and stands alone — it does not
    load guide-and-verify, does not hand off to it,
    and no file of guide-and-verify is touched"]
    Q -->|rejected| B["hand off to guide-and-verify at run time for
    the part a person does by hand — the new skill
    would then be built on it; ruled out by the owner:
    copy the necessary steps, do not build on it"]
    Q -->|rejected| C["give guide-and-verify an architecture mode —
    that edits a skill whose one job is hand-work in a
    console; ruled out by the owner: guide-and-verify
    must not change"]
```

A new skill is being designed whose output is the architecture document — with its
diagrams — for a new system that plugs into an existing one (named
`architect-and-verify` by ADR 0246). Its method comes from
`guide-and-verify`: measure the live system before writing, state the expected result
before anyone acts, check afterwards. Ruled by the owner 2026-10-03: the new skill only
copies the necessary steps from `guide-and-verify` and is not built on it, and
`guide-and-verify` must not change.

So the new skill carries its own text for every step it borrows, adapted to its own
domain, and has no run-time dependency on `guide-and-verify` — it never loads it and
never hands off to it. The accepted cost is drift: from the day of the copy the two are
separate texts, and a later change to `guide-and-verify` does not reach the new skill.
Which steps count as necessary is recorded separately, as it is decided.
