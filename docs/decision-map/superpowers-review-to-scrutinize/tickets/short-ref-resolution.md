---
title: Live check - does a bare sp- reference actually resolve to the plugin skill, on both harnesses?
type: task
mode: HITL
status: open
assignee: 
blocked_by: []
gist: 
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["short-ref-resolution (this ticket)"]
```
<!-- decision-map:graph:end -->

## Question

ADR 0071 and ADR 0072 both write every reference to the six copies in short form with no plugin prefix, on the argument that the sp- prefix is unique. That settles AMBIGUITY, not RESOLUTION: on Claude Code a plugin skill is surfaced and invoked as plugin:skill, and nobody has observed whether a bare "load the sp-writing-plans skill" instruction actually reaches it, or whether the model needs the qualified name. On Antigravity skills stage flat, so short form should be exact there - but that is also an assumption. Probe both harnesses the way skilloverrides-live-check did, with a measured run against a control, and record what was observed rather than what was expected. If short form does not resolve on Claude Code, ADR 0071 Decision 2 and ADR 0072 Decision 2 both need amending, and 11 references plus the 6 inside the copies change form.
