---
title: Naming - what are the copied skills called, and what do their descriptions trigger on?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [coexistence, skilloverrides-live-check, coexistence-mechanism]
gist: 
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["skill-naming (this ticket)"]
    P0["coexistence"] --> ME
    P1["coexistence-mechanism"] --> ME
    P2["skilloverrides-live-check"] --> ME
    ME --> C0["arc-rewiring"]
```
<!-- decision-map:graph:end -->

## Question

Do the copies keep the upstream skill names (brainstorming, writing-plans, requesting-code-review...) or take distinguishing names, and how are their description triggers written so the intended copy wins and the reference in a sibling skill stays unambiguous?
