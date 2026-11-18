---
title: Reliability - the session dies in the middle of a stage: what then?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [stage-model]
gist: 
---

## Question

A session can end or compact while a step of the do stage is half done, or while a loaded skill is running. Where is progress written so the next call continues from the right step and does not redo a step that already landed - the runbook's Outcome log, daily-state.md, or a file of its own?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["resume-after-break (this ticket)"]
    P0["stage-model"] --> ME
```
<!-- decision-map:graph:end -->
