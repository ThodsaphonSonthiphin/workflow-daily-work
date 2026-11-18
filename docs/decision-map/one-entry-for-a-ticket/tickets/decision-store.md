---
title: Decisions - runbook table, map ticket or ADR: which one is the record?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [which-map]
gist: 
---

## Question

Decisions now live in three places: the runbook's D1..Dn table, Decision tickets on a map, and ADRs. Which is the record for a decision about one ticket, which only link to it, and which of them does the check accept as a 'written, approved decision' (ADR 0324)?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["decision-store (this ticket)"]
    P0["which-map"] --> ME
```
<!-- decision-map:graph:end -->
