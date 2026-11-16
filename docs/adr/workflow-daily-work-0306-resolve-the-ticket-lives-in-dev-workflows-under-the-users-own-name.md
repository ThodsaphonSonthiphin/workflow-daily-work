# resolve-the-ticket lives in dev-workflows, under the user's own name

```mermaid
flowchart TD
    Q{"what is the skill called, and which plugin<br/>ships it?"} -->|chosen| A["skill resolve-the-ticket in dev-workflows, command
    /dev-workflows:resolve-the-ticket, one PLAYBOOK row,
    one row in the /daily WORK table. The name is the
    user's: 'Create a skill called Resolve the Ticket'"]
    Q -->|rejected| B["ado-backlog - the skill reads two trackers and loads
    ticket-trace, read-picture and guide-and-verify, all
    in dev-workflows; ado-backlog is the findings
    pipeline and writes to the board, which this never
    does"]
    Q -->|rejected| C["a name that says 'check' (ready-to-resolve,
    ticket-check) - more exact, since the skill never
    sets the State, but the user named it, and the
    description says in its first line what it does not
    do"]
```

Decided 2026-11-16 in the grilling session; the name is the user's (Pon), the placement is
the agent's, following where the skills it loads already live. Two collisions are closed in
the description and the glossary, not by renaming: `work-map` *resolves* a **Decision
ticket** (a different thing, a different plugin), and "resolve" here never means the skill
changes the State (ADR 0295).
