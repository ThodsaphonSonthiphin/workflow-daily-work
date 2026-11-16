# resolve-the-ticket never writes to the tracker; on READY it drafts the closing comment

```mermaid
flowchart TD
    Q{"the check ends with a table and a verdict.<br/>What may the skill do to the ticket on the board?"} -->|chosen| A["nothing. On READY it gives the closing comment as raw
    Markdown in one code block, in the project's own
    comment format when its CLAUDE.md defines one. The
    person pastes it, ticks the AC and sets the State"]
    Q -->|rejected| B["post the comment and set State = Resolved after an
    explicit yes - a State change is the one act a second
    person relies on; it stays a human's click, so the
    skill can never be the thing that resolved a ticket
    its own check got wrong"]
    Q -->|rejected| C["post the comment only, after a yes - half a write:
    it adds an auth path and a format risk (the REST API
    does not render Markdown as the editor does) to save
    one paste"]
```

Ruled 2026-11-16 by the user (Pon), taking the recommended option. The skill is read-only
against the tracker in both moments, as `why-this-logic` is (ADR 0281). On NOT READY no
comment is drafted - there is nothing to close. The draft follows the traced project's own
comment rules where they exist (the user's project fixes a shape in its `CLAUDE.md`: a
result heading with the UTC time, how it was checked, an `| Item | Result |` table, and
"details in the runbook" instead of a copy of it).
