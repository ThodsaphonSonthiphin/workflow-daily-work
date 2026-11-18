# The no-runbook hand-off asks guide-and-verify for the file, not for a runbook session

> **Narrowed 2026-11-18 by ADR 0341.** The file-only hand-off now applies in one case: the check is asked for on a ticket whose work was done with no runbook. In the do-and-verify stage guide-and-verify runs in full and creates the runbook.

```mermaid
flowchart TD
    Q{"the ticket has no runbook. What does the hand-off<br/>to guide-and-verify ask it for?"} -->|chosen| A["the runbook file only - in its own shape and the
    project's naming, holding the title, the ticket
    link, the file list and the boundary line - with no
    baseline measurement and nothing written to the
    ticket. This skill then appends its block"]
    Q -->|rejected| B["a full guide-and-verify run - its measure-the-
    baseline phase has nothing to measure once the work
    is done, and it writes readings onto the ticket,
    which breaks this skill's read-only promise (ADR 0318)"]
    Q -->|rejected| C["this skill writes the file itself - the user ruled
    that guide-and-verify owns runbooks (ADR 0326)"]
```

Ruled 2026-11-16 by the controller during execution of the resolve-the-ticket plan, after
the final whole-branch review. Amends ADR 0326, which stays in force otherwise: the runbook
still comes from `guide-and-verify`, in its shape and the project's naming, and this skill
still never authors one.

Evidence: the review found that ADR 0326's hand-off, read as "run guide-and-verify",
starts a session whose first phase measures the system before a change. At the check the
change is already made, so that baseline would record the after state as the before state,
and the session posts its readings on the ticket - a tracker write this skill promises never
to make. Asking for the file alone keeps both promises and gives the check block a home.
