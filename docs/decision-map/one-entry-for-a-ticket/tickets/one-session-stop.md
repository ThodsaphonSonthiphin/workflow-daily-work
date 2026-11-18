---
title: The stop rule - how does one entry respect 'one session, then stop'?
type: grilling
mode: HITL
status: closed
assignee: stop-rule-grill-2103
blocked_by: []
gist: The entry's own run ends wherever chart-map or work-map stops; the next call reads the Feature's map and proposes the plan stage again until no Decision ticket is open.
---

## Question

chart-map ends its session after charting, and work-map resolves exactly one HITL ticket and stops. A single call that walks a whole ticket would run past both stops. Does the entry skill end its own run at each of those stops and resume on the next call, or do the map skills get a mode that returns to the caller?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["one-session-stop (this ticket)"]
```
<!-- decision-map:graph:end -->

<!-- decision-map:resolution:start -->
## Resolution

The entry's own run ends wherever chart-map or work-map stops; the next call reads the Feature's map and proposes the plan stage again until no Decision ticket is open.

Detail: docs/adr/workflow-daily-work-0348-the-entrys-run-ends-wherever-a-map-skill-stops.md

```mermaid
flowchart TD
    C["a call in the plan stage"] --> M{"the Feature's map"}
    M -->|"none yet"| CH["load chart-map - the map is charted"]
    M -->|"open Decision tickets"| WM["load work-map - one ticket resolved"]
    M -->|"none left open"| D["propose do and verify"]
    CH --> E["the run ends: one line says what is left<br/>and that the next call carries on"]
    WM --> E
    X["displaced: asking 'go on now?' at the stop"] -.-> E
```

Confirming exchange, 2026-11-18: the user picked "A. จบรอบเสมอ" over asking "go on now?" at each stop (the agent's recommendation).

<!-- decision-map:resolution:end -->
