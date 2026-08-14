---
title: Host plugin - do the copies live in dev-workflows or a new plugin of their own?
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
    ME["host-plugin (this ticket)"]
    ME --> C0["antigravity-install"]
    ME --> C1["convention-compliance"]
```
<!-- decision-map:graph:end -->

## Question

Do the vendored skills land inside plugins/dev-workflows (one plugin, but six large foreign skills mixed into the daily arc) or in a new plugin such as superpowers-local (its own manifest, marketplace entry, version and one-time enable step)? Decide against the repo's existing plugin boundaries, not just file tidiness.
