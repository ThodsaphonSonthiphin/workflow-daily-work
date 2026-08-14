---
title: Coexistence - does the superpowers plugin stay enabled alongside the copies?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [harness-skill-shadowing]
gist: 
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["coexistence (this ticket)"]
    P0["harness-skill-shadowing"] --> ME
    ME --> C0["arc-rewiring"]
    ME --> C1["copy-granularity"]
    ME --> C2["skill-naming"]
```
<!-- decision-map:graph:end -->

## Question

Do we keep superpowers@claude-plugins-official enabled and accept two copies of brainstorming / writing-plans / the review skills competing for the same triggers, or disable it and take over every skill we depend on (including the ones with no review step)? The answer sets the naming, the copy granularity and how much of the daily arc has to be repointed.
