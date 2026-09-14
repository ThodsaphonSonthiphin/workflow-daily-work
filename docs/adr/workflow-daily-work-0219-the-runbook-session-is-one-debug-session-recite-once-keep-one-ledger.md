# The runbook session is one debug session — recite once, keep one ledger

```mermaid
flowchart TD
    Q{a second step fails in the same runbook:<br/>is that a new debug session?} -->|chosen| A["no — the runbook session IS the debug session:
    the freeze line goes out again, step ① re-enters,
    but the mantra is not re-recited and the ledger
    continues, because the earlier runs are still
    evidence (same system, same person, same console)"]
    Q -->|rejected| B["each failed step is its own debug session —
    recite again, start a fresh ledger: a plain
    reading of debug-mantra, and a wall of text for
    a person already tired and clicking, with the
    step-2 runs thrown away before step 6"]
```

`debug-mantra` recites the mantra and the diagram *once per debug session, in the first
response*, and does not define a session when a runbook surrounds it. Ruled 2026-09-14, on the
caller's side only (ADR 0216): the whole `guide-and-verify` runbook session is one debug
session. The first failed after-check gets the ADR 0215 freeze and the full recital; every
later failed step in the same runbook gets the freeze and re-enters at step ① with the ledger
it already has — no second recital, no fresh ledger. The runs from an earlier failed step stay
evidence for a later one because the system, the person and the console are the same, which
is exactly what step ④ cross-references. Nothing in `debug-mantra` changes; this is the
caller's reading of the word *session*.
