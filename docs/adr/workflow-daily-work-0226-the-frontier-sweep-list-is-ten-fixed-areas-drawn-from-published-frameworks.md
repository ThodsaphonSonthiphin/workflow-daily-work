# The frontier sweep list is ten fixed areas drawn from published frameworks, without usability or maintainability, and one list for every destination

```mermaid
flowchart TD
    Q{what does the sweep of ADR 0222<br/>actually sweep?} -->|chosen| A["ten fixed areas, each with two or three
    probe questions, kept in one skill-relative
    reference file: scope & non-goals · functional
    gaps · performance & capacity · reliability &
    recovery · security & threat · identity &
    authorization · data & privacy · deploy & change
    safety · operations & observability ·
    dependencies, cost & compliance — the union of
    ISO 25010:2023, Google's SRE launch checklist and
    design-doc cross-cutting concerns, the AWS/Azure
    Well-Architected pillars and OWASP's four
    threat-modelling questions"]
    Q -->|rejected| B["twelve areas, adding usability/accessibility
    and maintainability — usability arrives on a map
    as a user-led prototype ticket already, and
    maintainability is a code-level property, not a
    decision to take before starting; both lengthen
    the one batched question the sweep is allowed"]
    Q -->|rejected| C["a list per destination kind — migration,
    greenfield, integration — no live map has yet
    shown one list to be insufficient; split later,
    when one does"]
```

The sweep needs a list, and the list is where the user's original complaint lives:
non-functional, functional, security, RBAC, backup and rollback, deployment limits.
Those six map onto four of the ten areas above; the other six — scope and
non-goals, data and privacy, operations, dependencies, cost, compliance — are what
every surveyed framework asks and the complaint did not name, which is the argument
for a fixed list over the user's own memory. The list lives in a reference file
beside chart-map's SKILL.md, addressed skill-relatively, and each area carries two
or three probe questions phrased in the user's terms so the batched sweep question
can quote them. Usability and maintainability are left out on purpose, and the
list is one list; both are recorded here as the places to reopen first if a real
map shows the sweep missing something.
