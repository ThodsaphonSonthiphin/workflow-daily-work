# The family walk is for a Feature or an Epic, and is asked about on GitHub

```mermaid
flowchart TD
    Q{"ADR 0351 walks the children of a Feature one at a<br/>time. A User Story with child Tasks also has<br/>children. Which tickets get the family walk?"} -->|chosen| A["Azure DevOps: a ticket of type Feature or Epic that
    has children. A User Story or Bug with child Tasks is
    walked as one ticket - its Tasks stay rows of its own
    check. GitHub: an issue with sub-issues is asked
    about once - walk them one at a time, or one ticket"]
    Q -->|rejected| B["every ticket with children - a story's Tasks are
    steps of one piece of work; a run each would brief
    and check the same change four times"]
    Q -->|rejected| C["decide on GitHub from a label - no label is the
    same in every repo"]
```

Ruled 2026-11-18 by the controller while writing the implementation plan
(`docs/superpowers/plans/2026-11-18-resolve-the-ticket-one-entry.md`). ADR 0351 names "a
Feature with several child tickets" and its example is Feature #193 with stories #194-#197;
the existing check already treats a story's child Task as one row (ADR 0321, eval 0). This
ADR only draws the line between the two. The user has not ruled on it; it is the agent's
reading and is flagged to the user with the plan.
