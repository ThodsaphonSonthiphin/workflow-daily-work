# After a break the entry reads the loaded skill's own record, and a step with no result is measured before it is done again

```mermaid
flowchart TD
    Q{"a session ends or compacts in the middle of the do<br/>stage. On the next call, where does resolve-the-ticket<br/>find how far the work got?"} -->|chosen| A["in the record the loaded skill already writes: the
    runbook's outcome lines for click work; the plan, its
    ledger and the git log for code work. A step with no
    result may have landed - it is measured first, never
    done again blind"]
    Q -->|rejected| B["a progress file of its own, one per ticket - the
    entry does not run the steps, so it cannot write
    'step 3 started' in time, and two records can disagree"]
    Q -->|rejected| C["daily-state.md - that file belongs to /daily and is
    kept by day, not by ticket"]
```

Ruled 2026-11-18 by the user (Pon), on Decision ticket `resume-after-break` of the map
`docs/decision-map/one-entry-for-a-ticket/`: "A. อ่านบันทึกของสกิลที่โหลด", from three
options the agent laid out.

| the work | the record read | what "may have landed" looks like |
|---|---|---|
| click work | the runbook: each step's outcome line, with its measurement and time (`guide-and-verify`, phase 5) | the first step with no outcome line |
| code work | the plan file, the executing skill's ledger, `git log` | a task with a commit but no ledger entry, or uncommitted changes in the tree |

On such a call the entry says what it found in one line ("steps 1-2 have a result, step 3
has none - it may have partly landed"), and hands that to the skill it loads with the
request to measure first. For click work this is `guide-and-verify`'s own rule already - a
redo destroys the state that tells not-saved from not-applied. The stage itself is still
found as [ADR 0337](workflow-daily-work-0337-resolve-the-ticket-walks-four-stages-and-reads-the-runbook-to-know-which-comes-next.md)
says.

Known limit: no record says a step was *started*, only that it *finished*. The rule above
is what covers the gap.

**Not yet in the skill.** It lands when the map's `do-and-verify` milestone is built.
