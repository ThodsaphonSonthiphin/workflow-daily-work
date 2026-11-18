---
title: Acting - what replaces 'builds nothing'?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: []
gist: 
---

## Question

ADR 0316 says resolve-the-ticket builds and fixes nothing. As the one entry it will lead work. May it act itself, or only through a skill it loads - and which acts stay a person's alone (the tracker, a live system the agent may only read, guide-and-verify's 'who acts' boundary)?

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["acting-rule (this ticket)"]
    ME --> C0["code-work-stage"]
    ME --> C1["who-did-what"]
```
<!-- decision-map:graph:end -->
