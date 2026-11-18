# On NOT READY the skill names the next skill per kind of gap, and stops

> **Amended 2026-11-18 by ADR 0339.** After NOT READY the skill now offers the skill for each gap and loads it on the person's yes.

```mermaid
flowchart TD
    Q{"the check says NOT READY. What does the skill do<br/>with the gaps?"} -->|chosen| A["one line per kind of gap, naming every row of that
    kind and the skill that closes it, then stop: no test
    -> generating-test-cases; failing test -> debug-mantra;
    stale pass -> the test step to run again; differs with
    no decision -> grill-then-plan; open child -> this
    skill on the child. It fixes nothing"]
    Q -->|rejected| B["start the skill for the first gap without asking -
    the order of the list is not the user's priority, and
    a check that starts repairs is no longer a check"]
    Q -->|rejected| C["list the gaps and name no skill - the person then
    has to know the playbook by heart at the moment they
    are most likely to press Resolved anyway"]
```

Ruled 2026-11-16 by the user (Pon), taking the recommended option. The shape is
`why-this-logic`'s closing offer (at most one line per kind, every ID of that kind named).
The skill never invokes the named skill itself; the user does.
