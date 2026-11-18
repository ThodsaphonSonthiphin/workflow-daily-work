# The read helpers are loaded without a yes

```mermaid
flowchart TD
    Q{"ADR 0339 says the skill loads a skill only after<br/>the person says yes. Step 1 of every run loads<br/>ticket-trace and read-picture to read the ticket.<br/>Do those two need a yes?"} -->|chosen| A["no. The yes is for a skill that does work. The two
    read helpers only fetch the ticket and open its
    images, as they have since the first release"]
    Q -->|rejected| B["ask before every load - a question before the skill
    has read anything, on every call, about a read the
    person asked for by giving the URL"]
    Q -->|rejected| C["copy the fetch steps into this skill so nothing is
    loaded - copies another skill's text (ruled out on
    the map) and drifts"]
```

Ruled 2026-11-18 by the controller during execution of
`docs/superpowers/plans/2026-11-18-resolve-the-ticket-one-entry.md`, after a task review
found the new line "never loads a skill without a yes" contradicted step 1. It reads
ADR 0339's "nothing more than today" as covering the two read helpers. The user has not
ruled on it; it is flagged to the user with the finished branch.
