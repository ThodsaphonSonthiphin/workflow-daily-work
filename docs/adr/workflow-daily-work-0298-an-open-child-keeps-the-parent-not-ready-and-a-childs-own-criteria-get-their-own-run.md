# An open child keeps the parent not ready; a child's own criteria get their own run

```mermaid
flowchart TD
    Q{"the ticket has child tickets. What does an open<br/>child do to the check of its parent?"} -->|chosen| A["each child is one row with its State. A child not in
    a done State keeps the parent NOT READY, unless the
    user says it stays open on purpose (marked told and
    written into the drafted closing comment). The child's
    own AC are not checked in this run"]
    Q -->|rejected| B["check every child's AC and logic in the same run -
    one table then judges several tickets, each with its
    own runbook; a run on the child does that with the
    same skill"]
    Q -->|rejected| C["list the children for information only - a parent
    could then be resolved over a child task nobody did,
    which is what the user's step 1 (include the child
    ticket) is there to catch"]
```

Ruled 2026-11-16 by the user (Pon), taking the recommended option. "Done State" is read from
the tracker's own state category, not from a fixed word - Resolved, Closed and Done differ
by process (see **Project** in `CONTEXT.md`). Amended by ADR 0307: a State named `Resolved`
also counts as done, because a measured process files it under the InProgress category. Real case used: #151 (User Story, Active) with
child #297 (Task, New).
