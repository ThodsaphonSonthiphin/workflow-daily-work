---
title: Antigravity - does install-antigravity.py cover the copies, or need a new rewrite shape?
type: task
mode: HITL
status: open
assignee: 
blocked_by: [host-plugin, override-distribution]
gist: 
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["antigravity-install (this ticket)"]
    P0["host-plugin"] --> ME
    P1["override-distribution"] --> ME
```
<!-- decision-map:graph:end -->

## Question

install-antigravity.py currently installs dev-workflows only and rewrites just the /references/, /scripts/ and /skills/ ${CLAUDE_PLUGIN_ROOT} shapes. Establish what the vendored skills actually reference, whether any new shape is needed in rewrite_plugin_root(), and what has to change for the copies to install under Antigravity.
