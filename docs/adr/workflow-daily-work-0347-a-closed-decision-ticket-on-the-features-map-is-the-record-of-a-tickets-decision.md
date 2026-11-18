# A closed Decision ticket on the Feature's map is the record of a ticket's decision

```mermaid
flowchart TD
    Q{"a decision about one tracker ticket can sit in the<br/>runbook's D1..Dn table, in a Decision ticket on a map,<br/>and in an ADR. Which is the record, and which does the<br/>check accept as a written, approved decision?"} -->|chosen| A["the closed Decision ticket on the Feature's map is
    the record - work-map writes it, with the person's
    confirming words. The check accepts it, and still
    accepts what it accepted before: an ADR, a runbook
    decision table, a ticket comment naming who approved"]
    Q -->|rejected| B["the runbook's table is the record - someone would
    have to copy each decision from the map into it, and
    the entry skill does not act (ADR 0339)"]
    Q -->|rejected| C["no record is named; anything with an approver's name
    counts - the same decision can then be written twice
    and drift"]
```

Ruled 2026-11-18 by the user (Pon), on Decision ticket `decision-store` of the map
`docs/decision-map/one-entry-for-a-ticket/`: "A. Decision ticket บน map", from three options
the agent laid out.

| place | role |
|---|---|
| closed Decision ticket on the Feature's map (ADR 0346) | the record of a decision about one tracker ticket |
| ADR | the canonical text where `work-map` produced one; the Decision ticket links to it |
| runbook's D1..Dn table | not written for new work; one that exists is still accepted - no runbook is converted |
| tracker comment naming who approved | still accepted |

This widens [ADR 0324](workflow-daily-work-0324-a-difference-from-the-ticket-passes-only-under-a-written-decision.md):
`pass - differs by decision <id>` may now cite a Decision ticket by its key and path. An
**open** or **claimed** Decision ticket is not a decision; only a closed one counts.

**In the skill since dev-workflows 0.66.0** (`plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md`).
