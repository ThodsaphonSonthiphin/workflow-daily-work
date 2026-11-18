---
title: Code-only work - what does the do stage load when no one has to click?
type: grilling
mode: HITL
status: closed
assignee: code-work-grill-2043
blocked_by: [acting-rule]
gist: Code work loads sp-writing-plans with the ticket's AC lines as requirements, then its executing skill; the tests it leaves are the proof the check reads.
---

## Question

guide-and-verify is for changes a person makes by hand in a console, and says not to use it for changes the agent can make itself. For a ticket whose work is code the agent can write: which skill does the do stage load, and is the before / after measurement of guide-and-verify still required there?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["code-work-stage (this ticket)"]
    P0["acting-rule"] --> ME
```
<!-- decision-map:graph:end -->

<!-- decision-map:resolution:start -->
## Resolution

Code work loads sp-writing-plans with the ticket's AC lines as requirements, then its executing skill; the tests it leaves are the proof the check reads.

Detail: docs/adr/workflow-daily-work-0342-for-code-work-the-do-stage-loads-the-plan-writing-line.md

```mermaid
flowchart TD
    E["resolve-the-ticket, do stage"] --> K{"what kind of work?<br/>(proposed, the person confirms)"}
    K -->|"a person must click"| G["guide-and-verify"]
    K -->|"code the agent can write"| P["sp-writing-plans<br/>requirements = the ticket's AC lines and logic rules"]
    P --> X["its executing skill:<br/>sp-subagent-driven-development or sp-executing-plans"]
    X --> T["tests in the repo = the proof the check reads"]
    G --> R["runbook steps and outcome lines = the proof the check reads"]
```

Confirming exchange, 2026-11-18: the user picked "A. สายเขียนแผน" over loading nothing, and over guide-and-verify for every ticket.

The agent's reading, not a separate answer from the user: no before / after measurement is asked of code work (the loaded skill's own rules apply, ADR 0339); the kind of work is proposed with the stage and confirmed in the same question; the row list is handed over as in ADR 0340.

<!-- decision-map:resolution:end -->
