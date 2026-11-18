# When chart-map says no map is needed, the person names the next stage

```mermaid
flowchart TD
    Q{"the plan stage offers chart-map whenever group 1 or<br/>2 has a point (ADR 0345). On a small ticket chart-map<br/>stops by its own rule: no map needed. No map exists,<br/>so the next call proposes the plan again. What ends<br/>the loop?"} -->|chosen| A["the person. The run ends with one line that says the
    next call will propose the plan again and that naming
    do and verify goes on. Nothing is written to record
    the stop"]
    Q -->|rejected| B["write a 'plan skipped' line into the runbook - a
    ticket at this point often has no runbook yet (ADR
    0341), so the record would exist only sometimes"]
    Q -->|rejected| C["fall back to grill-then-plan inside the same run -
    a second shape of decision beside the Decision ticket,
    which ADR 0349 rejected for the not-installed case"]
    Q -->|rejected| D["never offer chart-map on a small ticket - the size
    question was the option the user did not take
    (ADR 0345)"]
```

Ruled 2026-11-18 by the controller during execution of
`docs/superpowers/plans/2026-11-18-resolve-the-ticket-one-entry.md`, after the final
whole-branch review walked this case and found the loop. ADR 0345 names the stop as known
and leaves the next call open; this is the smallest rule that closes it without a new
write and without editing `chart-map` (ADR 0338). The user has not ruled on it; it is
flagged to the user with the finished branch as the weakest of the three rulings.
