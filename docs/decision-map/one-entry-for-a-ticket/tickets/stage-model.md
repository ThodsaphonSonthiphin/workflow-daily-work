---
title: Stages - which stages does a ticket have, and how does a run know where it is?
type: grilling
mode: HITL
status: closed
assignee: stage-model-grill-2032
blocked_by: []
gist: Four stages - briefing, plan, do and verify, check; on each call the skill reads the runbook, proposes the next stage with one line of evidence, and asks once.
---

## Question

Today the skill asks 'briefing or check' (ADR 0317). With a planning stage and a do-and-verify stage in between: what are the stages, what ends each one, and when the skill is called again on the same ticket how does it know which stage comes next - by asking, by reading the runbook, or by the ticket's State?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["stage-model (this ticket)"]
    ME --> C0["map-trigger"]
    ME --> C1["resume-after-break"]
```
<!-- decision-map:graph:end -->

<!-- decision-map:resolution:start -->
## Resolution

Four stages - briefing, plan, do and verify, check; on each call the skill reads the runbook, proposes the next stage with one line of evidence, and asks once.

Detail: docs/adr/workflow-daily-work-0337-resolve-the-ticket-walks-four-stages-and-reads-the-runbook-to-know-which-comes-next.md

```mermaid
flowchart TD
    C["resolve-the-ticket is called with a ticket URL"] --> R["read the ticket's runbook"]
    R --> P["say which stage comes next, with one line of evidence,<br/>and ask once - the person may name another stage"]
    P --> S1["1. briefing<br/>ends: the person says go on"]
    S1 --> S2["2. plan (skipped when nothing to decide)<br/>ends: no open point left to decide"]
    S2 --> S3["3. do and verify<br/>ends: every runbook step has a recorded result"]
    S3 --> S4["4. check<br/>ends: READY, the person resolves"]
    X["displaced: the question 'briefing or check?' (ADR 0317)"] -.-> P
```

Confirming exchange, 2026-11-18:

- Stages: the user picked "4 ช่วงตามตาราง" over three stages (plan inside the briefing) and five (do apart from verify).
- Knowing the stage: the user picked "A. อ่าน runbook แล้วเสนอ" over asking every time, the ticket's State, and reading without asking.
- While answering, the user added a rule for the whole map: "ต้องไม่แก้สกิลเก่านะ" - "ห้ามแก้ทุกสกิล ยกเว้น resolve ticket". It is ADR 0338.

The briefing writes no file today, so it gains one line in the runbook - in resolve-the-ticket's own text only.

Not decided here: when the plan stage is skipped (`map-trigger`), and where progress inside a stage is written (`resume-after-break`).

<!-- decision-map:resolution:end -->
