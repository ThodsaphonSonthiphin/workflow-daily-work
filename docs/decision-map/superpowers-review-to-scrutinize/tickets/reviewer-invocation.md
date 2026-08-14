---
title: Invocation - how does a dispatched reviewer subagent run a frozen, human-facing scrutinize?
type: grilling
mode: HITL
status: open
assignee: 
blocked_by: []
gist: 
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["reviewer-invocation (this ticket)"]
```
<!-- decision-map:graph:end -->

## Question

Touchpoints #3, #4 and #5 dispatch a reviewer subagent against a prompt FILE (code-reviewer.md, task-reviewer-prompt.md, re-review-prompt.md), while scrutinize is a human-facing SKILL.md at effort max that is frozen by decision. Does each prompt file become a thin wrapper telling the subagent to load scrutinize, does it inline scrutinize's stance, or something else - and what carries the per-touchpoint context (merge base, plan file, task number) that the prompts supply today?
