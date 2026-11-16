# A row passes on a written result, a test run now, or the user's word - each marked

```mermaid
flowchart TD
    Q{"what must exist for one AC line or logic rule<br/>to count as PASS in the check?"} -->|chosen| A["any of three, and the row says which: CITED - a
    result written in the runbook, a ticket comment or a
    test file, with its locator and date; MEASURED - a
    test the skill ran in this session; TOLD - the user
    says it was tested (who, date). The verdict line,
    READY TO RESOLVE: YES (N rows rest on your word),
    counts the rows that rest on a person's word"]
    Q -->|rejected| B["a written result or a run only; a told row keeps the
    ticket NOT READY - recommended; the user ruled that
    their word counts. Much of this testing is by hand in
    a console, and a rule that refuses the tester's word
    gets worked around by writing a line nobody checks"]
    Q -->|rejected| C["only what is tested again in this session - most
    tests here are hand-made steps in a live system;
    repeating all of them at every check costs hours and
    changes test data"]
```

Ruled 2026-11-16 by the user (Pon): "Your word counts too". The three marks are
`why-this-logic`'s **Proof mark** words with the same meanings (ADRs 0263, 0266, 0272), so
no new vocabulary is added. What keeps a told pass honest is that it is never shown as
anything else: the row carries `told: <who>, <date>`, the verdict reads
`READY TO RESOLVE: YES (N rows rest on your word)`, and the drafted closing comment carries the same mark.
