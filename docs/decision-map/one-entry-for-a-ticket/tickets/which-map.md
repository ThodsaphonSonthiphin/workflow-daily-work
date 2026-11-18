---
title: Which map - the project's map, or one per ticket?
type: grilling
mode: HITL
status: closed
assignee: which-map-grill-2101
blocked_by: [map-trigger]
gist: One map per Feature, shared by all its children; a ticket with no Feature above it gets its own map; folder and ticket keys carry the tracker numbers.
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

<!-- decision-map:resolution:start -->
## Resolution

One map per Feature, shared by all its children; a ticket with no Feature above it gets its own map; folder and ticket keys carry the tracker numbers.

Detail: docs/adr/workflow-daily-work-0346-a-tickets-decisions-go-on-one-map-per-feature.md

```mermaid
flowchart TD
    F["Feature #193"] --> M["one map: docs/decision-map/ado-193-&lt;short name&gt;/"]
    C1["child #195"] -->|"key 195-..."| M
    C2["child #196"] -->|"key 196-..."| M
    S["a ticket with no Feature above it"] --> O["a map of its own: ado-&lt;id&gt;-&lt;short name&gt;/"]
    X["displaced: adding to the project's existing map; a map per ticket"] -.-> M
```

Confirming exchange, 2026-11-18: the user picked "C. map ต่อ Feature" over a new map per ticket, and over the project's existing map.

The folder and key names are the agent's proposal (ADR 0346 says so). The map's fog line about a Feature with several children is half answered: decisions are kept together; how the stages walk a family is still open.

<!-- decision-map:resolution:end -->
