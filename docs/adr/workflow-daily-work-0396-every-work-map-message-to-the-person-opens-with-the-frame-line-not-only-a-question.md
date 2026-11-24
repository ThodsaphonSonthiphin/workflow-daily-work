# Every work-map message to the person opens with the Frame line, not only a question

```mermaid
flowchart TD
    Q{"work-map sends the person four kinds of message: the<br/>frontier, the dry-run gate, a grilling question and the<br/>close report. Which of them open with the Frame line?"} -->|chosen| A["all four. A message that is not one question carries
    the line without a question number - '#196 AC-2 ·
    196-match-key closed · plan: #196 has 7 open' - so one
    rule covers every message: it opens with the Frame line"]
    Q -->|rejected| B["questions only - the first /wait-what of 2026-11-24
    (10:03) came on the dry-run report, not on a question,
    and a rule that must say which messages count is a
    second rule to keep"]
```

Ruled 2026-11-24 by the user (Pon): "a", from two options the agent laid out, in the same
grill-then-plan session as ADRs 0392-0395. The agent recommended A.

The line's parts stay those of ADR 0392; "question N of M" is present only on a question,
and "of M" only when the asker knows M. On the frontier and the close report the tracker
part is the ticket the session was called for (ADR 0394) when there is one.
