---
title: Granularity - whole skill directories, or just the reviewer prompt files with shims?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [coexistence]
gist: 
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["copy-granularity (this ticket)"]
    P0["coexistence"] --> ME
    ME --> C0["convention-compliance"]
    ME --> C1["resync-path"]
```
<!-- decision-map:graph:end -->

## Question

Do we vendor all six affected skill directories wholesale (~2100 lines, including 250-line brainstorming and 568-line subagent-driven-development that are mostly unrelated to review), or copy only the four reviewer prompt files plus thin skills that delegate the rest to superpowers? Weigh the maintenance surface against the coupling each option leaves behind.
