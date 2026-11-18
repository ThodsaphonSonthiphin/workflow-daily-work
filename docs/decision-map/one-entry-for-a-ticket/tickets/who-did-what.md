---
title: Identity - how is it recorded who did each step and who approved each decision?
type: grilling
mode: HITL
status: closed
assignee: identity-grill-2054
blocked_by: [acting-rule]
gist: No gathered record is added: who did a step stays in each skill's own record, and the check table and closing comment stay as they are.
---

## Question

guide-and-verify logs a step the agent made at the person's request as an Exception; the check marks a pass cited / measured / told. Across the whole line: what one record shows, per step and per decision, whether a person or the agent did it and who approved it - and does the closing comment carry it?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["who-did-what (this ticket)"]
    P0["acting-rule"] --> ME
```
<!-- decision-map:graph:end -->

<!-- decision-map:resolution:start -->
## Resolution

No gathered record is added: who did a step stays in each skill's own record, and the check table and closing comment stay as they are.

Detail: docs/adr/workflow-daily-work-0344-who-did-a-step-stays-in-each-skills-own-record-and-the-check-gathers-none-of-it.md

```mermaid
flowchart TD
    G["guide-and-verify: exception lines<br/>(a step the agent made at the person's request)"] --> K["each record stays where it is"]
    C["code work: commits and the agreed plan"] --> K
    D["decisions: ADR / Decision ticket with the quoted approval"] --> K
    K --> N["the check table and the closing comment: unchanged,<br/>no 'done by' column"]
    X["displaced: nothing - a gathered record was proposed and not taken"] -.-> N
```

Confirming exchange, 2026-11-18: the user picked "C. ไม่รวม" over a 'done by' column in the runbook's check block (the agent's recommendation) and over the full column in the closing comment too. No reason was given.

<!-- decision-map:resolution:end -->
