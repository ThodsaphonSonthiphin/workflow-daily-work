---
title: decision-map not installed - what does the planning stage do?
type: grilling
mode: HITL
status: closed
assignee: plugin-missing-grill-2104
blocked_by: [cross-plugin-loading]
gist: The plan stage says the map skills are not installed, prints the install line for each channel and ends the run; no fallback without a map and no silent skip.
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

<!-- decision-map:resolution:start -->
## Resolution

The plan stage says the map skills are not installed, prints the install line for each channel and ends the run; no fallback without a map and no silent skip.

Detail: docs/adr/workflow-daily-work-0349-with-the-map-skills-not-installed-the-plan-stage-stops-with-the-install-line.md

```mermaid
flowchart TD
    P["plan stage needs chart-map / work-map"] --> K{"are the skills available in this session?"}
    K -->|yes| L["load on the person's yes"]
    K -->|no| S["say so, print the install line for<br/>Claude Code, npx and Antigravity, end the run"]
    S --> N["the person installs, or names another stage"]
    X["displaced: deciding without a map; skipping the stage"] -.-> S
```

Confirming exchange, 2026-11-18: the user picked "A. หยุดพร้อมคำสั่งติดตั้ง" over falling back to sp-grill-with-doc, and over skipping the plan stage.

The detection, the short-form names and the three-channel install line are the agent's reading of the research ticket cross-plugin-loading (ADR 0349 says so). No channel has a live test on record.

<!-- decision-map:resolution:end -->
