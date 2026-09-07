# Equally eligible drill classes are ordered by the research ranking

```mermaid
flowchart TD
    Q{"ADR 0198 selects drill classes by collapse<br/>state. On the first run NO class has any<br/>exposure, so all nine are in full form and<br/>equally eligible - and the sitting must pick<br/>five. What breaks the tie?"}
    Q -->|chosen| A["The expected-frequency ranking from ticket<br/>#16 - article, sv-agreement, preposition,<br/>plural, word-choice, verb-tense, copula,<br/>existential, capitalisation. On day one it<br/>is the only evidence there is. A TIEBREAK,<br/>never a weighting."]
    Q -->|rejected| B["Random. Neutral and needs no justification,<br/>but it spends the first sitting - the one<br/>with the most attention behind it - on<br/>whatever came up, when a documented<br/>expectation about this population exists."]
    Q -->|rejected| C["Use the ranking as a standing weight, not<br/>just a tiebreak. That is what ADR 0198<br/>rejected: frequency measures how often a<br/>class FIRES, not whether it has been<br/>learned, so `article` would be drilled<br/>forever."]
```

Found by tracing a first sitting by hand during the build of ticket #23. Selecting by collapse
state, as [ADR 0198](workflow-daily-work-0198-drill-items-are-chosen-by-collapse-state-not-frequency.md)
requires, does not discriminate when every class has the *same* state — and on the first run
every class has zero exposure days, so all nine are in full form at once. Eight of them have a
documented seed and the sitting needs five. Nothing said which five.

The ranking from ticket #16 fills the gap with the only evidence available at that moment. It
is an expected-frequency order for Thai-L1 writers, derived from the cited literature, and on
day one there is no user-specific data to prefer over it.

**It is a tiebreak and must stay one.** ADR 0198 rejected frequency as a *selector* for a
reason that has not changed: frequency measures how often a class fires, not whether it has
been learned, so ranking by it would drill `article` forever. The moment two classes differ in
collapse state, that difference decides and the ranking is not consulted. It is consulted only
between classes the collapse state cannot separate.

The ranking's own weakness is worth restating, since this is the one place it is load-bearing:
#16 recorded it as **low-confidence**, reasoning over a register nobody has studied, and noted
that genre can invert rank within a single cohort. That is acceptable here precisely because
it only ever chooses between options already judged equal, and because it is displaced by real
data as soon as any exists.
