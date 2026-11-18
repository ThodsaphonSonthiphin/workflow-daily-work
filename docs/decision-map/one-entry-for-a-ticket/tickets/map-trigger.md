---
title: Planning - when does a ticket open or touch a decision map?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [stage-model]
gist: 
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
