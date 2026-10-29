# The provenance check is named `why-this-logic`

```mermaid
flowchart TD
    Q{what is the skill called?} -->|chosen| A["why-this-logic - the words the user already
    asks in; one line different from ticket-trace,
    which answers why for one line, where this
    breaks the logic into rows"]
    Q -->|rejected| B["logic-provenance - exact, but a noun, and
    hard to say in a chat"]
    Q -->|rejected| C["trace-and-teach - names both halves, but
    hides that the main output is a verdict table"]
```

Chosen 2026-10-29. The skill lives at `plugins/dev-workflows/skills/why-this-logic/` and is
invoked as `/why-this-logic <thing> [source]`. ADRs 0261-0264 that say "the provenance-check
skill (name pending)" mean this skill.
