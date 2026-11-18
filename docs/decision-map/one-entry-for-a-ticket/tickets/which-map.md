---
title: Which map - the project's map, or one per ticket?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [map-trigger]
gist: 
---

## Question

A project can already have a map (the user's has one with 14 tickets). Do a ticket's decisions go onto that map or onto a new map for the ticket, and how does a Decision ticket name the tracker ticket it touches, so the briefing and the check can find it later?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["which-map (this ticket)"]
    P0["map-trigger"] --> ME
    ME --> C0["decision-store"]
```
<!-- decision-map:graph:end -->
