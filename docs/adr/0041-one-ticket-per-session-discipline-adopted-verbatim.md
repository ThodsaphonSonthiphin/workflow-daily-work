# ADR 0041 — decision-map adopts the one-ticket-per-session discipline verbatim

- **Status:** Accepted
- **Date:** 2026-07-31

```mermaid
flowchart TD
    Q{"how strict is the<br/>session discipline?"} -->|chosen| FULL["upstream-verbatim: one HITL ticket<br/>per session (research subagents<br/>excepted); charting is its own session<br/>and hand-resolves nothing"]
    Q -->|rejected| SOFT["guideline with small-ticket<br/>exceptions — answers start living in<br/>conversation memory instead of the<br/>map; the map stops being the<br/>state carrier"]
    Q -->|rejected| NONE["no cap — if one session can hold<br/>many decisions, the effort didn't<br/>need a map at all"]
```

The cap is what makes the map the **only** state carrier — the same "replay, don't
re-derive" principle ADR 0014 fixed for daily-state. The pull to resolve "just one
more" is redefined as a signal: either the frontier is genuinely small (the map is
nearly done) or the session is overreaching. `daily-state.md` may point at the
claimed ticket by name as its focus line, but the map and the tracker's
assignee/state fields remain the source of truth for effort progress.
