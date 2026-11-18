---
title: Planning - when does a ticket open or touch a decision map?
type: grilling
mode: HITL
status: closed
assignee: map-trigger-grill-2059
blocked_by: [stage-model]
gist: Open points of group 1 (as task tickets) and group 2 (as grilling tickets) go on a Decision map through chart-map; when both are empty the plan stage is skipped, said in one line.
---

## Question

The briefing sorts open points into four groups (ADR 0336). Which of them become Decision tickets on a map - only 'decide while designing', or 'fix before the work starts' too - and when there are none, is the planning stage skipped without a word?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["map-trigger (this ticket)"]
    P0["stage-model"] --> ME
    ME --> C0["which-map"]
```
<!-- decision-map:graph:end -->

<!-- decision-map:resolution:start -->
## Resolution

Open points of group 1 (as task tickets) and group 2 (as grilling tickets) go on a Decision map through chart-map; when both are empty the plan stage is skipped, said in one line.

Detail: docs/adr/workflow-daily-work-0345-the-plan-stage-puts-every-open-point-of-groups-one-and-two-on-a-decision-map.md

```mermaid
flowchart TD
    B["briefing: open points in four groups"] --> G1["1. fix before the work starts"]
    B --> G2["2. decide while designing"]
    B --> G3["3. rules to keep"]
    B --> G4["4. touches no task"]
    G1 -->|"task ticket - ask the person named"| M["Decision map (chart-map, on the person's yes)"]
    G2 -->|"grilling ticket"| M
    G3 -.->|"no ticket"| N["stay in the briefing"]
    G4 -.->|"no ticket"| N
    B -->|"groups 1 and 2 both empty"| S["plan stage skipped - said in one line"]
```

Confirming exchange, 2026-11-18: the user picked "B. กลุ่ม 1 + 2" over group 2 only, and over group 2 with a size question (the agent's recommendation).

Known: chart-map's own no-fog stop still applies on a small ticket; it may not be edited.

<!-- decision-map:resolution:end -->
