---
title: Resync - what is the documented procedure for pulling upstream changes into the copies?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [copy-granularity]
gist: 
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["resync-path (this ticket)"]
    P0["copy-granularity"] --> ME
```
<!-- decision-map:graph:end -->

## Question

What provenance do the copies record (upstream sha, per-file origin, a manifest?), and what is the written procedure for diffing a newer obra/superpowers against them and re-applying the scrutinize routing? Name where that procedure lives and who runs it.
