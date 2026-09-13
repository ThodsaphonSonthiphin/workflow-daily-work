# The handoff maps what it already holds onto the four steps, and ranks saved-is-not-applied first

```mermaid
flowchart TD
    Q{what does guide-and-verify tell the agent it<br/>already has, when debug-mantra opens?} -->|chosen| A["a four-row mapping: ① the before/after
    measurements ARE the repro and the environment
    is the runbook's named one; ② the step's own
    numbered actions are the fail path; ③ hypothesis
    #1 is always the saved-is-not-applied trap — read
    the pending state first; ④ the per-check
    measurements on the ticket are the ledger"]
    Q -->|rejected| B["hand over the measurements only and leave
    hypothesis ranking to the agent — the agent
    then asks the person for a repro it was just
    given, and reaches for 'wrong record' before
    the cheapest disproof"]
    Q -->|rejected| C["mandate the whole ranked list (trap, skipped
    line, wrong object, propagation delay) — over-fits
    six kinds of system to one order; only the first
    entry is the same everywhere"]
```

`debug-mantra` step ① stops when there is no repro and asks the user for one; entered from a
failed after-check, the repro already exists — the baseline and the after-measurement, taken
read-only in a second channel — and the environment is the one the runbook names. Ruled
2026-09-14: `guide-and-verify`'s handoff text says this mapping out loud so the agent does not
re-ask for what it holds, and it fixes exactly one hypothesis: **#1 is the saved-is-not-applied
trap**, because the skill already carries its six-system table, it explains most failed checks,
and its disproof is one read of the pending state. Everything after #1 stays the agent's to
rank, per the mantra's own step ③.
