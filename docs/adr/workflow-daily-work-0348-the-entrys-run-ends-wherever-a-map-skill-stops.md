# The entry's run ends wherever a map skill stops

```mermaid
flowchart TD
    Q{"chart-map ends its session after charting and<br/>work-map resolves one HITL ticket and stops. Neither<br/>may be edited (ADR 0338). What does resolve-the-ticket<br/>do when one of them stops?"} -->|chosen| A["its own run ends there, every time. It says in one
    line what is left and that the next call carries on.
    The next call reads the Feature's map, counts the
    open Decision tickets and proposes the plan stage
    again, until none is left"]
    Q -->|rejected| B["at the stop it asks 'go on now?' and loads the next
    skill on a yes - recommended; the user chose the
    plain stop"]
    Q -->|rejected| C["the map skills get a mode that returns to the caller
    - needs an edit to them"]
```

Ruled 2026-11-18 by the user (Pon), on Decision ticket `one-session-stop` of the map
`docs/decision-map/one-entry-for-a-ticket/`: "A. จบรอบเสมอ", from two options the agent laid
out. The agent recommended the first rejected branch.

One call, in the plan stage, does one of these and then ends:

| the Feature's map | the call |
|---|---|
| does not exist, and groups 1 or 2 have points (ADR 0345) | loads `chart-map`; the map is charted; the run ends |
| has open Decision tickets | loads `work-map`; one ticket is resolved; the run ends |
| has none left open | the plan stage is over; the entry proposes do and verify |

How the next call knows: it reads the map the way it reads the runbook
([ADR 0337](workflow-daily-work-0337-resolve-the-ticket-walks-four-stages-and-reads-the-runbook-to-know-which-comes-next.md)) -
the count of open Decision tickets is the plan stage's evidence line.

**In the skill since dev-workflows 0.66.0** (`plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md`).
