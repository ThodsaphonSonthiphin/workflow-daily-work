---
title: decision-map not installed - what does the planning stage do?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [cross-plugin-loading]
gist: 
---

## Question

resolve-the-ticket ships in dev-workflows; chart-map and work-map ship in the decision-map plugin. When decision-map is not installed (or only single skills were installed through npx): does the planning stage stop with an install line, fall back to the runbook's decision table, or skip?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["plugin-missing (this ticket)"]
    P0["cross-plugin-loading"] --> ME
```
<!-- decision-map:graph:end -->
