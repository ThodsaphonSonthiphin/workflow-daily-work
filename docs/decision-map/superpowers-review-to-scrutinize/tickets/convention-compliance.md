---
title: Conventions - how far must vendored copies obey this repo's skill conventions?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: [copy-granularity, host-plugin]
gist: 
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["convention-compliance (this ticket)"]
    P0["copy-granularity"] --> ME
    P1["host-plugin"] --> ME
```
<!-- decision-map:graph:end -->

## Question

The repo requires harness-neutral wording, ${CLAUDE_PLUGIN_ROOT} only in the three shapes the Antigravity installer rewrites, an opening Mermaid diagram on generated documents, and one PLAYBOOK.md row per skill. Which of these bind a vendored foreign skill, given that every deviation from upstream text is a line the resync has to reconcile forever?
