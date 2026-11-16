# A difference from the ticket passes only under a written decision

```mermaid
flowchart TD
    Q{"what was built differs from what the ticket says.<br/>How is that row judged at the check?"} -->|chosen| A["a written, approved decision that covers the
    difference - a runbook decision, an ADR, a ticket
    comment - makes the row read 'differs by decision
    #lt;id#gt;' and it passes when its test passes. Every such
    row is listed in the drafted closing comment. A
    difference with no written decision is DIFFERS and
    keeps the ticket NOT READY"]
    Q -->|rejected| B["any difference keeps the ticket NOT READY until the
    ticket text is changed - the ticket is often another
    person's to edit, and the decision already says why"]
    Q -->|rejected| C["do not compare the ticket with the build; ask only
    for a passing test - a test of the wrong rule passes"]
```

Ruled 2026-11-16 by the user (Pon), taking the recommended option. Real case used: #151's
ticket gives the 7-day cut-off as a UTC day; runbook decision D2, approved 2026-11-09, built
it on the Melbourne date following the Tech Spec. The comparison itself uses
`why-this-logic`'s verdict words - a row that *contradicts* its source with no decision is
this ADR's DIFFERS. A decision counts only when it is written and says who approved it; the
user's word given during the check closes the row as told, the same as ADR 0319.
